"""Reads that exist only to answer the dashboard's two questions: what needs doing now, and what lands next."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from clock import BUSINESS_TZ, business_now, utcnow
from database import get_db
from dependencies import get_current_user
from models import (
    ChangeRequest,
    ChangeRequestStatus,
    Client,
    FieldworkSnapshot,
    Project,
    ProjectAssignment,
    ProjectMarket,
    Role,
    Stage,
    User,
)
from schemas import DashboardSummary, QueueCounts, UpcomingItem

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Stages whose dates no longer need chasing.
_CLOSED = (Stage.DELIVERED, Stage.ON_HOLD)


@router.get("/upcoming", response_model=list[UpcomingItem])
def upcoming(
    days: int = Query(2, ge=1, le=30, description="How far ahead to look"),
    include_overdue: bool = True,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Every dated commitment in one ordered list.

    Four different columns across two tables answer "what lands next", and the whole
    value is in the ordering across all of them — which is why this is one endpoint
    rather than the frontend fetching four lists and interleaving them itself.
    """
    now = utcnow()
    horizon = now + timedelta(days=days)
    floor = None if include_overdue else now

    def in_window(column):
        clauses = [column.isnot(None), column <= horizon]
        if floor is not None:
            clauses.append(column >= floor)
        return clauses

    items: list[UpcomingItem] = []

    project_dates = (
        ("client_eta", "Link to client", Project.client_link_eta),
        ("field_close", "Fieldwork closes", Project.expected_field_end_date),
        ("merged_delivery", "Merged delivery", Project.final_delivery_date),
    )
    for kind, label, column in project_dates:
        rows = (
            db.query(Project, Client.name)
            .join(Client, Client.id == Project.client_id)
            .filter(Project.stage.notin_(_CLOSED), *in_window(column))
            .all()
        )
        items += [
            UpcomingItem(
                kind=kind,
                label=label,
                due_at=getattr(p, column.key),
                project_id=p.id,
                rdr_number=p.rdr_number,
                survey_name=p.survey_name,
                client=client_name,
                stage=p.stage,
            )
            for p, client_name in rows
        ]

    market_rows = (
        db.query(ProjectMarket, Project, Client.name)
        .join(Project, Project.id == ProjectMarket.project_id)
        .join(Client, Client.id == Project.client_id)
        .filter(
            Project.stage.notin_(_CLOSED),
            ProjectMarket.delivered_at.is_(None),
            *in_window(ProjectMarket.due_date),
        )
        .all()
    )
    items += [
        UpcomingItem(
            kind="market_due",
            label=f"{market.country} due",
            due_at=market.due_date,
            project_id=project.id,
            rdr_number=project.rdr_number,
            survey_name=project.survey_name,
            client=client_name,
            stage=project.stage,
        )
        for market, project, client_name in market_rows
    ]

    items.sort(key=lambda i: i.due_at)
    return items


@router.get("/counts", response_model=QueueCounts)
def counts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sidebar badges in one call rather than one request per queue."""
    by_stage = {
        stage.value: 0 for stage in Stage
    }
    for stage, total in db.query(Project.stage, func.count(Project.id)).group_by(Project.stage):
        by_stage[stage.value] = total

    pm_role = select(Role.id).where(Role.name == "pm").scalar_subquery()
    claimed_by_pm = select(ProjectAssignment.project_id).where(
        ProjectAssignment.role_id == pm_role,
        ProjectAssignment.unassigned_at.is_(None),
    )
    pool = (
        db.query(func.count(Project.id))
        .filter(Project.stage == Stage.PM_ASSIGNMENT, Project.id.notin_(claimed_by_pm))
        .scalar()
        or 0
    )

    scripter_role = select(Role.id).where(Role.name == "scripter").scalar_subquery()
    claimed_by_scripter = select(ProjectAssignment.project_id).where(
        ProjectAssignment.role_id == scripter_role,
        ProjectAssignment.unassigned_at.is_(None),
    )
    scripting_unclaimed = (
        db.query(func.count(Project.id))
        .filter(Project.stage == Stage.SCRIPTING, Project.id.notin_(claimed_by_scripter))
        .scalar()
        or 0
    )

    ours = select(ProjectAssignment.project_id).where(
        ProjectAssignment.user_id == user.id,
        ProjectAssignment.unassigned_at.is_(None),
    )
    mine = (
        db.query(func.count(Project.id))
        .filter(Project.id.in_(ours), Project.stage.notin_((Stage.DELIVERED,)))
        .scalar()
        or 0
    )

    return QueueCounts(
        pool=pool,
        scripting_unclaimed=scripting_unclaimed,
        by_stage=by_stage,
        mine=mine,
    )


# Soft launch is a band, not a moment: between 10% and 30% fielded and not yet
# confirmed, the PM owes it a review. Below 10% it is too early to judge; at 30%
# the decision has effectively been made by letting it run.
SOFT_LAUNCH_FLOOR = 10
SOFT_LAUNCH_CEILING = 30


def _business_day_bounds(offset_days: int = 0) -> tuple[datetime, datetime]:
    """Start and end of a UK day, returned as naive UTC to match the stored columns."""
    local = business_now() + timedelta(days=offset_days)
    start_local = local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    return (
        start_local.astimezone(UTC).replace(tzinfo=None),
        end_local.astimezone(UTC).replace(tzinfo=None),
    )


def _deliverables_between(db: Session, start, end, project_ids=None) -> int:
    """Count deliverables, not projects: one project can owe several dates in a day."""
    project_q = db.query(func.count(Project.id)).filter(
        Project.stage.notin_(_CLOSED),
        Project.final_delivery_date.isnot(None),
        Project.final_delivery_date >= start,
        Project.final_delivery_date < end,
    )
    market_q = (
        db.query(func.count(ProjectMarket.id))
        .join(Project, Project.id == ProjectMarket.project_id)
        .filter(
            Project.stage.notin_(_CLOSED),
            ProjectMarket.delivered_at.is_(None),
            ProjectMarket.due_date.isnot(None),
            ProjectMarket.due_date >= start,
            ProjectMarket.due_date < end,
        )
    )
    eta_q = db.query(func.count(Project.id)).filter(
        Project.stage.in_((Stage.SCRIPTING, Stage.QA)),
        Project.client_link_eta.isnot(None),
        Project.client_link_eta >= start,
        Project.client_link_eta < end,
    )
    if project_ids is not None:
        project_q = project_q.filter(Project.id.in_(project_ids))
        market_q = market_q.filter(Project.id.in_(project_ids))
        eta_q = eta_q.filter(Project.id.in_(project_ids))
    return (project_q.scalar() or 0) + (market_q.scalar() or 0) + (eta_q.scalar() or 0)


def _overdue(db: Session, now, project_ids=None) -> int:
    project_q = db.query(func.count(Project.id)).filter(
        Project.stage.notin_(_CLOSED),
        Project.final_delivery_date.isnot(None),
        Project.final_delivery_date < now,
    )
    market_q = (
        db.query(func.count(ProjectMarket.id))
        .join(Project, Project.id == ProjectMarket.project_id)
        .filter(
            Project.stage.notin_(_CLOSED),
            ProjectMarket.delivered_at.is_(None),
            ProjectMarket.due_date.isnot(None),
            ProjectMarket.due_date < now,
        )
    )
    eta_q = db.query(func.count(Project.id)).filter(
        Project.stage.in_((Stage.SCRIPTING, Stage.QA)),
        Project.client_link_eta.isnot(None),
        Project.client_link_eta < now,
    )
    if project_ids is not None:
        project_q = project_q.filter(Project.id.in_(project_ids))
        market_q = market_q.filter(Project.id.in_(project_ids))
        eta_q = eta_q.filter(Project.id.in_(project_ids))
    return (project_q.scalar() or 0) + (market_q.scalar() or 0) + (eta_q.scalar() or 0)


def _soft_launch_due(db: Session) -> int:
    """Live, still on SOFT_LAUNCH, and the latest reading sits in the review band."""
    latest = (
        db.query(
            FieldworkSnapshot.project_id,
            func.max(FieldworkSnapshot.captured_at).label("captured_at"),
        )
        .group_by(FieldworkSnapshot.project_id)
        .subquery()
    )
    return (
        db.query(func.count(FieldworkSnapshot.id))
        .join(
            latest,
            (FieldworkSnapshot.project_id == latest.c.project_id)
            & (FieldworkSnapshot.captured_at == latest.c.captured_at),
        )
        .join(Project, Project.id == FieldworkSnapshot.project_id)
        .filter(
            Project.stage == Stage.LIVE,
            Project.sub_status == "SOFT_LAUNCH",
            FieldworkSnapshot.percent_complete >= SOFT_LAUNCH_FLOOR,
            FieldworkSnapshot.percent_complete < SOFT_LAUNCH_CEILING,
        )
        .scalar()
        or 0
    )


@router.get("/summary", response_model=DashboardSummary)
def summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Every tile on the dashboard, counted once, server-side.

    The tiles, the filtered lists they link to, and the project page all have to agree
    about what "due today" means — so the definition lives here rather than in the UI.
    Days are UK days (ADR 0011), not the viewer's.
    """
    now = utcnow()
    today_start, today_end = _business_day_bounds()
    tomorrow_start, tomorrow_end = _business_day_bounds(1)

    by_stage = {stage.value: 0 for stage in Stage}
    for stage, total in db.query(Project.stage, func.count(Project.id)).group_by(Project.stage):
        by_stage[stage.value] = total
    active = sum(
        count for stage, count in by_stage.items()
        if stage not in (Stage.DELIVERED.value, Stage.ON_HOLD.value)
    )

    ours = select(ProjectAssignment.project_id).where(
        ProjectAssignment.user_id == user.id,
        ProjectAssignment.unassigned_at.is_(None),
    )

    return DashboardSummary(
        due_today=_deliverables_between(db, today_start, today_end),
        due_tomorrow=_deliverables_between(db, tomorrow_start, tomorrow_end),
        overdue=_overdue(db, now),
        soft_launch_due=_soft_launch_due(db),
        active=active,
        by_stage=by_stage,
        my_due_today=_deliverables_between(db, today_start, today_end, ours),
        my_overdue=_overdue(db, now, ours),
        my_active=(
            db.query(func.count(Project.id))
            .filter(Project.id.in_(ours), Project.stage.notin_(_CLOSED))
            .scalar()
            or 0
        ),
        open_change_requests=(
            db.query(func.count(ChangeRequest.id))
            .filter(ChangeRequest.status != ChangeRequestStatus.COMPLETED)
            .scalar()
            or 0
        ),
        as_of=now,
    )
