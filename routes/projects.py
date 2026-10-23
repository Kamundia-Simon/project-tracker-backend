"""Project pool endpoint handling creation of projects, pools and PM self-asignment."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from dependencies import get_current_user, require_global_role, user_project_roles, user_global_roles
from constants import (
    CHECKLISTS,
    CHECKLIST_COLUMNS,
    CHECKLIST_ITEM_IDS,
    CHECKLIST_STATES,
    DERIVED_ITEM_IDS,
    SURVEY_TYPES,
    REQUIRED_ITEM_IDS,
    SUB_STATUSES,
)
from database import get_db
from models import AuditLog, Client, Project, ProjectAssignment, Revision, Role, Stage, StageTransition, User
from schemas import ProjectCreate, ProjectOut, ProjectPoolItem, ProjectDetail, ProjectOwner, AssignmentCreate, AssignmentOut, SelfAssign, ChecklistUpdate, EtaSet, ChangesRequested, TransitionOut, OwnerBrief, ProjectListItem, ProjectPage
from datetime import datetime

from clock import to_db, utcnow

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("/pool", response_model=list[ProjectPoolItem])
def list_pool(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log of projects that have just been created but not picked up by a PM yet"""
    pm_role_id = select(Role.id).where(Role.name == "pm").scalar_subquery()
    claimed = select(ProjectAssignment.project_id).where(
            ProjectAssignment.role_id == pm_role_id,
            ProjectAssignment.unassigned_at.is_(None),
        )
    return (
        db.query(Project)
        .filter(Project.stage == Stage.PM_ASSIGNMENT, Project.id.notin_(claimed))
        .order_by(Project.created_at)
        .all()
    )


def _project_detail(db: Session, project: Project) -> ProjectDetail:
    rows = (
        db.query(User.id, User.name, User.email, Role.name)
        .join(ProjectAssignment, ProjectAssignment.user_id == User.id)
        .join(Role, Role.id == ProjectAssignment.role_id)
        .filter(
            ProjectAssignment.project_id == project.id,
            ProjectAssignment.unassigned_at.is_(None),
        )
        .order_by(Role.name, User.name)
        .all()
    )
    owners = [
        ProjectOwner(user_id=uid, name=name, email=email, role=role)
        for uid, name, email, role in rows
    ]
    return ProjectDetail(
        **ProjectOut.model_validate(project).model_dump(),
        owners=owners,
    )

@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Full project record, including everyone currently assigned to it."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    return _project_detail(db, project)

@router.post("/{project_id}/send-to-scripting", response_model=ProjectDetail)
def send_to_scripting(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hand a fully logged project to the scripting queue — the owning PM makes this call."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")

    if "pm" not in user_project_roles(db, user, project_id) and "admin" not in user_global_roles(db, user):
        raise HTTPException(403, "Only this project's PM can send it to scripting")

    if project.stage != Stage.PM_ASSIGNMENT:
        raise HTTPException(409, f"Project has already left PM assignment (now {project.stage.value})")

    if not project.survey_type:
        raise HTTPException(422, "Set a survey type before sending this project to scripting")

    db.add(
        StageTransition(
            project_id=project_id,
            from_stage=project.stage,
            to_stage=Stage.SCRIPTING,
            from_sub_status=project.sub_status,
            changed_by=user.id,
        )
    )
    project.stage = Stage.SCRIPTING
    project.sub_status = None
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


def _checklist_gaps(project: Project, name: str) -> list[str]:
    """Item ids still waiting on a decision — neither done nor marked not applicable."""
    state = getattr(project, CHECKLIST_COLUMNS[name]) or {}
    return sorted(
        item_id for item_id in REQUIRED_ITEM_IDS[name]
        if state.get(item_id) not in CHECKLIST_STATES
    )


@router.patch("/{project_id}/checklists/{name}", response_model=ProjectDetail)
def update_checklist(
    project_id: int,
    name: str,
    payload: ChecklistUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark checklist items done or not applicable. Sending null clears an item."""
    if name not in CHECKLIST_COLUMNS or name not in CHECKLISTS:
        raise HTTPException(404, f"No checklist called {name}")

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")

    roles = user_project_roles(db, user, project_id) | user_global_roles(db, user)
    if not roles & {"pm", "scripter", "qa", "dp", "admin"}:
        raise HTTPException(403, "Only someone working on this project can tick its checklist")

    unknown = set(payload.items) - CHECKLIST_ITEM_IDS[name]
    if unknown:
        raise HTTPException(422, f"Unknown checklist items: {', '.join(sorted(unknown))}")

    derived = set(payload.items) & DERIVED_ITEM_IDS[name]
    if derived:
        raise HTTPException(
            422,
            f"{', '.join(sorted(derived))} ticks itself once everything else is answered",
        )

    bad = {v for v in payload.items.values() if v is not None and v not in CHECKLIST_STATES}
    if bad:
        raise HTTPException(422, f"A checklist item is {' or '.join(CHECKLIST_STATES)}, not: {', '.join(sorted(bad))}")

    column = CHECKLIST_COLUMNS[name]
    # Copy before mutating: SQLAlchemy does not notice in-place changes to a JSON column.
    state = dict(getattr(project, column) or {})
    for item_id, value in payload.items.items():
        if value is None:
            state.pop(item_id, None)
        else:
            state[item_id] = value
    # The sign-off follows the rest of the list rather than being claimed.
    everything_answered = all(
        state.get(item_id) in CHECKLIST_STATES for item_id in REQUIRED_ITEM_IDS[name]
    )
    for item_id in DERIVED_ITEM_IDS[name]:
        if everything_answered:
            state[item_id] = "done"
        else:
            state.pop(item_id, None)

    setattr(project, column, state)
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


@router.put("/{project_id}/eta", response_model=ProjectDetail)
def set_eta(
    project_id: int,
    payload: EtaSet,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The scripter's estimate covering scripting and QA — when the client gets the link."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")

    roles = user_project_roles(db, user, project_id) | user_global_roles(db, user)
    if not roles & {"scripter", "pm", "admin"}:
        raise HTTPException(403, "Only this project's scripter or PM can set the ETA")

    if project.stage not in (Stage.SCRIPTING, Stage.QA, Stage.CLIENT_REVIEW):
        raise HTTPException(409, f"An ETA belongs to the scripting and QA stages, not {project.stage.value}")

    eta = to_db(payload.client_link_eta)
    if eta <= utcnow():
        raise HTTPException(422, "That ETA is in the past")

    previous = project.client_link_eta
    project.client_link_eta = eta
    db.add(
        AuditLog(
            user_id=user.id,
            project_id=project_id,
            action="eta_set",
            field_name="client_link_eta",
            old_value=previous.isoformat() if previous else None,
            new_value=eta.isoformat(),
        )
    )
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


@router.post("/{project_id}/send-to-qa", response_model=ProjectDetail)
def send_to_qa(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hand a finished script to QA — the scripter's own sign-off that the work is done."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")

    roles = user_project_roles(db, user, project_id) | user_global_roles(db, user)
    if not roles & {"scripter", "pm", "admin"}:
        raise HTTPException(403, "Only this project's scripter can send it to QA")

    if project.stage != Stage.SCRIPTING:
        raise HTTPException(409, f"Project is not in scripting (now {project.stage.value})")

    if project.client_link_eta is None:
        raise HTTPException(422, "Set an ETA before sending this project to QA")

    gaps = _checklist_gaps(project, "scripting")
    if gaps:
        raise HTTPException(
            422,
            f"{len(gaps)} checklist item(s) still open: {', '.join(gaps)}",
        )

    db.add(
        StageTransition(
            project_id=project_id,
            from_stage=project.stage,
            to_stage=Stage.QA,
            from_sub_status=project.sub_status,
            changed_by=user.id,
        )
    )
    project.stage = Stage.QA
    project.sub_status = None
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


def _assignment_out(db: Session, assignment: ProjectAssignment) -> AssignmentOut:
    user, role_name = (
        db.query(User, Role.name)
        .join(Role, Role.id == assignment.role_id)
        .filter(User.id == assignment.user_id)
        .one()
    )
    return AssignmentOut(
        id=assignment.id,
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=role_name,
        assigned_at=assignment.assigned_at,
    )


@router.post("/{project_id}/assignments", response_model=AssignmentOut, status_code=201)
def assign_to_project(
    project_id: int,
    payload: AssignmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Put someone on this project in a given role. The PM staffs their own project."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")

    actor_roles = user_project_roles(db, user, project_id) | user_global_roles(db, user)
    if "pm" not in actor_roles and "admin" not in actor_roles:
        raise HTTPException(403, "Only this project's PM can assign people to it")

    role = db.query(Role).filter(Role.name == payload.role).first()
    if role is None:
        raise HTTPException(422, f"Unknown role: {payload.role}")

    assignee = db.get(User, payload.user_id)
    if assignee is None:
        raise HTTPException(422, "Unknown user")
    if not assignee.is_active:
        raise HTTPException(422, f"{assignee.name} is deactivated")

    current = (
        db.query(ProjectAssignment)
        .filter(
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.role_id == role.id,
            ProjectAssignment.unassigned_at.is_(None),
        )
        .all()
    )
    if any(a.user_id == assignee.id for a in current):
        raise HTTPException(409, f"{assignee.name} is already the {payload.role} on this project")

    # One accountable owner: every other role may be held by several people at once.
    if payload.role == "pm" and current:
        if "admin" not in user_global_roles(db, user) and not user.is_head_pm_override:
            raise HTTPException(409, "This project already has a project manager")
        for held in current:
            held.unassigned_at = utcnow()

    assignment = ProjectAssignment(project_id=project_id, user_id=assignee.id, role_id=role.id)
    db.add(assignment)
    db.add(
        AuditLog(
            user_id=user.id,
            project_id=project_id,
            action="assigned",
            field_name=payload.role,
            new_value=assignee.name,
        )
    )
    db.commit()
    db.refresh(assignment)
    return _assignment_out(db, assignment)


@router.delete("/{project_id}/assignments/{assignment_id}", response_model=list[AssignmentOut])
def unassign_from_project(
    project_id: int,
    assignment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Close out an assignment. The row stays — it is the record of who used to own this."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")

    actor_roles = user_project_roles(db, user, project_id) | user_global_roles(db, user)
    if "pm" not in actor_roles and "admin" not in actor_roles:
        raise HTTPException(403, "Only this project's PM can remove people from it")

    assignment = db.get(ProjectAssignment, assignment_id)
    if assignment is None or assignment.project_id != project_id:
        raise HTTPException(404, "Assignment not found on this project")
    if assignment.unassigned_at is not None:
        raise HTTPException(409, "That assignment is already closed")

    role_name = db.get(Role, assignment.role_id).name
    assignment.unassigned_at = utcnow()
    db.add(
        AuditLog(
            user_id=user.id,
            project_id=project_id,
            action="unassigned",
            field_name=role_name,
            old_value=db.get(User, assignment.user_id).name,
        )
    )
    db.commit()

    remaining = (
        db.query(ProjectAssignment)
        .filter(
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.unassigned_at.is_(None),
        )
        .all()
    )
    return [_assignment_out(db, a) for a in remaining]


def _owners_by_project(db: Session, project_ids: list[int]) -> dict[int, list[OwnerBrief]]:
    """One query for the whole page's owners — the alternative is a query per row."""
    if not project_ids:
        return {}
    rows = (
        db.query(ProjectAssignment.project_id, Role.name, User.name)
        .join(Role, Role.id == ProjectAssignment.role_id)
        .join(User, User.id == ProjectAssignment.user_id)
        .filter(
            ProjectAssignment.project_id.in_(project_ids),
            ProjectAssignment.unassigned_at.is_(None),
        )
        .order_by(Role.name, User.name)
        .all()
    )
    owners: dict[int, list[OwnerBrief]] = {}
    for project_id, role_name, user_name in rows:
        owners.setdefault(project_id, []).append(OwnerBrief(role=role_name, name=user_name))
    return owners


def _assigned_to(user_id: int):
    """Subquery of projects this person currently holds any role on."""
    return select(ProjectAssignment.project_id).where(
        ProjectAssignment.user_id == user_id,
        ProjectAssignment.unassigned_at.is_(None),
    )


SORTS = {
    "due": Project.final_delivery_date,
    "eta": Project.client_link_eta,
    "created": Project.created_at,
    "rdr": Project.rdr_number,
}


@router.get("", response_model=ProjectPage)
def list_projects(
    stage: Stage | None = None,
    unclaimed: str | None = Query(None, description="Role nobody currently holds, e.g. scripter"),
    mine: bool = False,
    assigned_to: int | None = Query(None, description="Anyone currently assigned to the project"),
    client_id: int | None = None,
    survey_type: str | None = None,
    due_before: datetime | None = Query(None, description="final_delivery_date earlier than this"),
    due_after: datetime | None = None,
    overdue: bool = Query(False, description="Delivery date passed and not yet delivered"),
    q: str | None = Query(None, description="Matches RDR number or survey name"),
    sort: str = Query("created", description="due | eta | created | rdr"),
    desc: bool = True,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Every queue in the app is this endpoint with different filters."""
    if sort not in SORTS:
        raise HTTPException(422, f"Cannot sort by {sort}. Use: {', '.join(SORTS)}")

    query = db.query(Project)

    if stage is not None:
        query = query.filter(Project.stage == stage)
    if client_id is not None:
        query = query.filter(Project.client_id == client_id)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(Project.rdr_number.like(pattern), Project.survey_name.like(pattern))
        )
    if unclaimed:
        role = db.query(Role).filter(Role.name == unclaimed).first()
        if role is None:
            raise HTTPException(422, f"Unknown role: {unclaimed}")
        held = select(ProjectAssignment.project_id).where(
            ProjectAssignment.role_id == role.id,
            ProjectAssignment.unassigned_at.is_(None),
        )
        query = query.filter(Project.id.notin_(held))
    if mine:
        query = query.filter(Project.id.in_(_assigned_to(user.id)))
    if assigned_to is not None:
        query = query.filter(Project.id.in_(_assigned_to(assigned_to)))
    if survey_type is not None:
        if survey_type not in SURVEY_TYPES:
            raise HTTPException(422, f"Unknown survey type: {survey_type}")
        query = query.filter(Project.survey_type == survey_type)
    if due_before is not None:
        query = query.filter(Project.final_delivery_date <= to_db(due_before))
    if due_after is not None:
        query = query.filter(Project.final_delivery_date >= to_db(due_after))
    if overdue:
        # Overdue means the promise passed while the work was still open — a delivered
        # project is never overdue, however late it was at the time.
        query = query.filter(
            Project.final_delivery_date.isnot(None),
            Project.final_delivery_date < utcnow(),
            Project.stage.notin_((Stage.DELIVERED, Stage.ON_HOLD)),
        )

    total = query.with_entities(func.count(Project.id)).scalar() or 0

    column = SORTS[sort]
    # Nulls last either way: a project with no date should not head the queue.
    query = query.order_by(column.is_(None), column.desc() if desc else column.asc())
    projects = query.offset(offset).limit(limit).all()

    owners = _owners_by_project(db, [p.id for p in projects])
    items = [
        ProjectListItem(
            **ProjectOut.model_validate(p).model_dump(
                include={
                    "id", "rdr_number", "survey_name", "client", "survey_type",
                    "stage", "sub_status", "client_link_eta", "final_delivery_date",
                }
            ),
            owners=owners.get(p.id, []),
        )
        for p in projects
    ]
    return ProjectPage(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate,
    user: User = Depends(require_global_role("pm")),
    db: Session = Depends(get_db),
):
    """Log a new project. The PM logging it takes it on unless they say otherwise."""
    if db.query(Project).filter(Project.rdr_number == payload.rdr_number).first():
        raise HTTPException(409, f"RDR number {payload.rdr_number} already exists")
    if db.get(Client, payload.client_id) is None:
        raise HTTPException(422, "Unknown client")

    project = Project(
        **payload.model_dump(exclude={"assign_me"}),
        created_by=user.id,
        stage=Stage.PM_ASSIGNMENT,
    )
    db.add(project)
    db.flush()

    if payload.assign_me:
        pm_role = db.query(Role).filter(Role.name == "pm").one()
        db.add(ProjectAssignment(project_id=project.id, user_id=user.id, role_id=pm_role.id))
        db.add(
            AuditLog(
                user_id=user.id,
                project_id=project.id,
                action="pm_self_assigned",
                new_value=user.name,
            )
        )

    db.commit()
    db.refresh(project)
    return project


# Claiming is for unclaimed work: the role, and the stage where that role's work happens.
CLAIMABLE = {"pm": Stage.PM_ASSIGNMENT, "scripter": Stage.SCRIPTING}
@router.post("/{project_id}/self-assign", response_model=ProjectOut)
def self_assign(
    project_id: int,
    payload: SelfAssign | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Claim unclaimed work — a PM picking up a new project, or a scripter taking one on."""
    role_name = (payload.role if payload else "pm")
    if role_name not in CLAIMABLE:
        raise HTTPException(422, f"{role_name} is not a role you can claim")

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")

    if role_name not in user_global_roles(db, user):
        raise HTTPException(403, f"You are not a {role_name}")

    expected_stage = CLAIMABLE[role_name]
    if project.stage != expected_stage:
        raise HTTPException(
            409,
            f"A {role_name} claims a project at {expected_stage.value}, "
            f"but this one is at {project.stage.value}",
        )

    role = db.query(Role).filter(Role.name == role_name).one()
    taken = (
        db.query(ProjectAssignment)
        .filter(
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.role_id == role.id,
            ProjectAssignment.unassigned_at.is_(None),
        )
        .first()
    )
    if taken:
        raise HTTPException(409, f"This project already has a {role_name}")

    db.add(ProjectAssignment(project_id=project_id, user_id=user.id, role_id=role.id))
    db.add(
        AuditLog(
            user_id=user.id,
            project_id=project_id,
            action=f"{role_name}_self_assigned",
            new_value=user.name,
        )
    )
    db.commit()
    db.refresh(project)
    return project


def _require_project_role(db: Session, user: User, project_id: int, *allowed: str) -> None:
    """Every gate asks the same question: does the caller hold one of these on this project?"""
    roles = user_project_roles(db, user, project_id) | user_global_roles(db, user)
    if not roles & set(allowed):
        raise HTTPException(403, f"This action is for: {', '.join(allowed)}")


def _transition(
    db: Session,
    project: Project,
    user: User,
    to_stage: Stage,
    to_sub_status: str | None = None,
    reason: str | None = None,
) -> None:
    """Record the move, then make it. stage_transitions is the project's timeline."""
    if to_sub_status is not None and to_sub_status not in SUB_STATUSES.get(to_stage.value, ()):
        raise HTTPException(422, f"{to_sub_status} is not a sub-status of {to_stage.value}")

    db.add(
        StageTransition(
            project_id=project.id,
            from_stage=project.stage,
            to_stage=to_stage,
            from_sub_status=project.sub_status,
            to_sub_status=to_sub_status,
            changed_by=user.id,
            reason=reason,
        )
    )
    project.stage = to_stage
    project.sub_status = to_sub_status


@router.post("/{project_id}/send-to-client", response_model=ProjectDetail)
def send_to_client(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm the link has been sent to the client — by email, outside this app.

    This records the handover; it does not perform it. See architecture.md section 5.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    # The PM owns the client relationship, so the PM confirms the handover.
    _require_project_role(db, user, project_id, "pm", "admin")

    if project.stage != Stage.QA:
        raise HTTPException(409, f"Project is not in QA (now {project.stage.value})")

    gaps = _checklist_gaps(project, "qa")
    if gaps:
        raise HTTPException(422, f"{len(gaps)} QA checklist item(s) still open: {', '.join(gaps)}")

    _transition(db, project, user, Stage.CLIENT_REVIEW, "AWAITING_CLIENT")
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


@router.post("/{project_id}/client-approved", response_model=ProjectDetail)
def client_approved(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The client signed off. Any open revision round closes with them."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    _require_project_role(db, user, project_id, "pm", "admin")

    if project.stage != Stage.CLIENT_REVIEW:
        raise HTTPException(409, f"Project is not with the client (now {project.stage.value})")

    open_round = (
        db.query(Revision)
        .filter(Revision.project_id == project_id, Revision.resolved_at.is_(None))
        .order_by(Revision.round_number.desc())
        .first()
    )
    if open_round:
        open_round.resolved_at = utcnow()

    _transition(db, project, user, Stage.QUOTAS)
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


@router.post("/{project_id}/client-changes", response_model=ProjectDetail)
def client_requested_changes(
    project_id: int,
    payload: ChangesRequested,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The client wants changes: log the round and send it back to scripting."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    _require_project_role(db, user, project_id, "pm", "admin")

    if project.stage != Stage.CLIENT_REVIEW:
        raise HTTPException(409, f"Project is not with the client (now {project.stage.value})")
    if not payload.summary.strip():
        raise HTTPException(422, "Say what the client asked for")

    last = (
        db.query(Revision)
        .filter(Revision.project_id == project_id)
        .order_by(Revision.round_number.desc())
        .first()
    )
    db.add(
        Revision(
            project_id=project_id,
            round_number=(last.round_number + 1) if last else 1,
            summary=payload.summary.strip(),
        )
    )
    # Back to scripting rather than a sub-status: the work is genuinely being redone.
    _transition(db, project, user, Stage.SCRIPTING, reason=payload.summary.strip())
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


@router.post("/{project_id}/launch", response_model=ProjectDetail)
def launch(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Open the survey at soft-launch size. Full launch is a separate, deliberate call."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    _require_project_role(db, user, project_id, "pm", "admin")

    if project.stage != Stage.QUOTAS:
        raise HTTPException(409, f"Project is not at quotas (now {project.stage.value})")

    _transition(db, project, user, Stage.LIVE, "SOFT_LAUNCH")
    project.live_start_date = utcnow()
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


@router.post("/{project_id}/confirm-soft-launch", response_model=ProjectDetail)
def confirm_soft_launch(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft launch checked out — open the quota to full. Stage does not change."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    _require_project_role(db, user, project_id, "pm", "admin")

    if project.stage != Stage.LIVE:
        raise HTTPException(409, f"Project is not live (now {project.stage.value})")
    if project.sub_status != "SOFT_LAUNCH":
        raise HTTPException(409, "This project is not in soft launch")

    _transition(db, project, user, Stage.LIVE, "FULL_LAUNCH")
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


@router.post("/{project_id}/hold", response_model=ProjectDetail)
def hold(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Park a project. Where it came from is recoverable from stage_transitions."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    _require_project_role(db, user, project_id, "pm", "admin")

    if project.stage == Stage.ON_HOLD:
        raise HTTPException(409, "Project is already on hold")
    if project.stage == Stage.DELIVERED:
        raise HTTPException(409, "A delivered project cannot be put on hold")

    _transition(db, project, user, Stage.ON_HOLD)
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


@router.post("/{project_id}/resume", response_model=ProjectDetail)
def resume(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Put a held project back where it was — read off the transition that parked it."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    _require_project_role(db, user, project_id, "pm", "admin")

    if project.stage != Stage.ON_HOLD:
        raise HTTPException(409, f"Project is not on hold (now {project.stage.value})")

    parked = (
        db.query(StageTransition)
        .filter(
            StageTransition.project_id == project_id,
            StageTransition.to_stage == Stage.ON_HOLD,
        )
        .order_by(StageTransition.changed_at.desc(), StageTransition.id.desc())
        .first()
    )
    if parked is None or parked.from_stage is None:
        raise HTTPException(409, "No record of where this project was before the hold")

    _transition(db, project, user, parked.from_stage, parked.from_sub_status)
    db.commit()
    db.refresh(project)
    return _project_detail(db, project)


@router.get("/{project_id}/transitions", response_model=list[TransitionOut])
def list_transitions(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """This project's timeline, newest first."""
    if db.get(Project, project_id) is None:
        raise HTTPException(404, "Project not found")

    rows = (
        db.query(StageTransition, User.name)
        .join(User, User.id == StageTransition.changed_by)
        .filter(StageTransition.project_id == project_id)
        .order_by(StageTransition.changed_at.desc(), StageTransition.id.desc())
        .all()
    )
    return [
        TransitionOut(
            id=t.id,
            from_stage=t.from_stage,
            to_stage=t.to_stage,
            from_sub_status=t.from_sub_status,
            to_sub_status=t.to_sub_status,
            changed_by=t.changed_by,
            changed_by_name=name,
            changed_at=t.changed_at,
            reason=t.reason,
        )
        for t, name in rows
    ]
