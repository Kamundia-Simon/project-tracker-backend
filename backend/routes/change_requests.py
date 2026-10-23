"""Post-delivery asks — crossbreaks, retabs, extra analysis — tracked beside the stage machinery, never inside it (ADR 0010)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from clock import to_db, utcnow
from database import get_db
from dependencies import get_current_user, user_global_roles
from models import ChangeRequest, ChangeRequestStatus, Client, Project, User
from schemas import ChangeRequestCreate, ChangeRequestOut, ChangeRequestUpdate

router = APIRouter(prefix="/api/change-requests", tags=["Change requests"])

# Whoever notices, logs it: the data team can record what a PM did not (ADR 0010).
_MAY_RAISE = {"pm", "dp", "admin"}


def _out(db: Session, cr: ChangeRequest) -> ChangeRequestOut:
    project, client_name = (
        db.query(Project, Client.name)
        .join(Client, Client.id == Project.client_id)
        .filter(Project.id == cr.project_id)
        .one()
    )
    raiser = db.get(User, cr.raised_by)
    assignee = db.get(User, cr.assigned_to) if cr.assigned_to else None
    return ChangeRequestOut(
        id=cr.id,
        project_id=cr.project_id,
        rdr_number=project.rdr_number,
        survey_name=project.survey_name,
        client=client_name,
        title=cr.title,
        description=cr.description,
        status=cr.status,
        raised_by=cr.raised_by,
        raised_by_name=raiser.name if raiser else "",
        assigned_to=cr.assigned_to,
        assigned_to_name=assignee.name if assignee else None,
        due_date=cr.due_date,
        created_at=cr.created_at,
        completed_at=cr.completed_at,
    )


@router.get("", response_model=list[ChangeRequestOut])
def list_change_requests(
    project_id: int | None = None,
    status: ChangeRequestStatus | None = None,
    mine: bool = Query(False, description="Only ones assigned to me"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Open work on a project, or a person's own queue — the two reads the indexes serve."""
    query = db.query(ChangeRequest)
    if project_id is not None:
        query = query.filter(ChangeRequest.project_id == project_id)
    if status is not None:
        query = query.filter(ChangeRequest.status == status)
    if mine:
        query = query.filter(ChangeRequest.assigned_to == user.id)
    rows = query.order_by(ChangeRequest.created_at.desc()).all()
    return [_out(db, cr) for cr in rows]


@router.post("", response_model=ChangeRequestOut, status_code=201)
def raise_change_request(
    payload: ChangeRequestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log a request against a delivered project. The project's stage does not move."""
    if not user_global_roles(db, user) & _MAY_RAISE:
        raise HTTPException(403, "Only a PM, the data team or an admin can raise a change request")
    if db.get(Project, payload.project_id) is None:
        raise HTTPException(422, "Unknown project")
    if not payload.title.strip():
        raise HTTPException(422, "Give the request a title")
    if payload.assigned_to is not None and db.get(User, payload.assigned_to) is None:
        raise HTTPException(422, "Unknown user")

    cr = ChangeRequest(
        project_id=payload.project_id,
        raised_by=user.id,
        title=payload.title.strip(),
        description=(payload.description or "").strip() or None,
        assigned_to=payload.assigned_to,
        due_date=to_db(payload.due_date) if payload.due_date else None,
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)
    return _out(db, cr)


@router.patch("/{change_request_id}", response_model=ChangeRequestOut)
def update_change_request(
    change_request_id: int,
    payload: ChangeRequestUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reassign, re-date, or move it along. Completing stamps completed_at."""
    cr = db.get(ChangeRequest, change_request_id)
    if cr is None:
        raise HTTPException(404, "Change request not found")
    if not user_global_roles(db, user) & _MAY_RAISE:
        raise HTTPException(403, "Only a PM, the data team or an admin can change this")

    data = payload.model_dump(exclude_unset=True)
    if "assigned_to" in data and data["assigned_to"] is not None:
        if db.get(User, data["assigned_to"]) is None:
            raise HTTPException(422, "Unknown user")
    if "title" in data:
        if not (data["title"] or "").strip():
            raise HTTPException(422, "Give the request a title")
        cr.title = data["title"].strip()
    if "description" in data:
        cr.description = (data["description"] or "").strip() or None
    if "assigned_to" in data:
        cr.assigned_to = data["assigned_to"]
    if "due_date" in data:
        cr.due_date = to_db(data["due_date"]) if data["due_date"] else None
    if "status" in data and data["status"] is not None:
        cr.status = data["status"]
        # completed_at follows the status rather than being set by hand.
        cr.completed_at = utcnow() if data["status"] == ChangeRequestStatus.COMPLETED else None

    db.commit()
    db.refresh(cr)
    return _out(db, cr)
