"""Pydantic request/response models — the shapes the API sends and receives, kept separate from models.py's database shapes."""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, field_validator, PlainSerializer

from models import ChangeRequestStatus, Stage
from constants import SURVEY_TYPES



def _with_utc_offset(value: datetime | None) -> str | None:
    """Stored values are naive UTC; the API always states the offset."""
    return None if value is None else value.replace(tzinfo=timezone.utc).isoformat()


UtcDatetime = Annotated[datetime, PlainSerializer(_with_utc_offset, return_type=str | None)]


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ClientCreate(BaseModel):
    name: str
    

class ProjectPoolItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rdr_number: str
    survey_name: str
    survey_type: str | None
    client: ClientOut
    created_at: UtcDatetime


class ProjectCreate(BaseModel):
    rdr_number: str
    survey_name: str
    client_id: int
    panel_criteria: str | None = None
    survey_type: str | None = None
    assign_me: bool = True

    @field_validator("survey_type")
    @classmethod
    def known_survey_type(cls, v: str | None) -> str | None:
        if v is not None and v not in SURVEY_TYPES:
            raise ValueError(f"Unknown survey type: {v}")
        return v


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rdr_number: str
    survey_name: str
    client: ClientOut
    panel_criteria: str | None
    survey_type: str | None
    stage: Stage
    sub_status: str | None
    client_link_eta: UtcDatetime | None
    final_delivery_date: UtcDatetime | None
    final_delivery_date_locked: bool
    target: int | None
    scripting_checklist_state: dict | None
    qa_checklist_state: dict | None
    quota_checklist_state: dict | None
    final_qa_checklist_state: dict | None
    created_by: int
    created_at: UtcDatetime
    updated_at: UtcDatetime


class MeOut(BaseModel):
    id: int
    email: str
    name: str
    timezone: str
    avatar: str | None
    is_head_pm_override: bool
    roles: list[str]


class MeUpdate(BaseModel):
    """What a user may change about themselves. Deliberately short."""
    avatar: str | None = None
    
    
class ProjectOwner(BaseModel):
    user_id: int
    name: str
    email: str
    role: str


class ProjectDetail(ProjectOut):
    owners: list[ProjectOwner]
    

class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    is_head_pm_override: bool
    roles: list[str]


class RoleGrant(BaseModel):
    role: str


class UserUpdate(BaseModel):
    is_active: bool | None = None
    is_head_pm_override: bool | None = None
    

class EtaSet(BaseModel):
    """A naive value is read as UK time — see ADR 0011."""
    client_link_eta: datetime


class ChecklistUpdate(BaseModel):
    """Item id to state: "done", "na", or null to clear a tick."""
    items: dict[str, str | None]


class AssignmentCreate(BaseModel):
    user_id: int
    role: str


class SelfAssign(BaseModel):
    role: str = "pm"

class AssignmentOut(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    role: str
    assigned_at: UtcDatetime


class OwnerBrief(BaseModel):
    """Just enough of an owner to render a queue row."""
    role: str
    name: str


class ProjectListItem(BaseModel):
    id: int
    rdr_number: str
    survey_name: str
    client: ClientOut
    survey_type: str | None
    stage: Stage
    sub_status: str | None
    client_link_eta: UtcDatetime | None
    final_delivery_date: UtcDatetime | None
    owners: list[OwnerBrief]


class ProjectPage(BaseModel):
    """A page of results plus the total, so the caller can show 'showing 25 of 84'."""
    items: list[ProjectListItem]
    total: int
    limit: int
    offset: int


class UpcomingItem(BaseModel):
    """One dated commitment, whatever kind of date it came from."""
    kind: str
    label: str
    due_at: UtcDatetime
    project_id: int
    rdr_number: str
    survey_name: str
    client: str
    stage: Stage


class QueueCounts(BaseModel):
    pool: int
    scripting_unclaimed: int
    by_stage: dict[str, int]
    mine: int


class ChangeRequestCreate(BaseModel):
    project_id: int
    title: str
    description: str | None = None
    assigned_to: int | None = None
    due_date: datetime | None = None


class ChangeRequestUpdate(BaseModel):
    """Partial: only the fields sent are touched."""
    title: str | None = None
    description: str | None = None
    status: ChangeRequestStatus | None = None
    assigned_to: int | None = None
    due_date: datetime | None = None


class ChangeRequestOut(BaseModel):
    id: int
    project_id: int
    rdr_number: str
    survey_name: str
    client: str
    title: str
    description: str | None
    status: ChangeRequestStatus
    raised_by: int
    raised_by_name: str
    assigned_to: int | None
    assigned_to_name: str | None
    due_date: UtcDatetime | None
    created_at: UtcDatetime
    completed_at: UtcDatetime | None


class DashboardSummary(BaseModel):
    """One definition of each tile, computed server-side so every view agrees."""
    due_today: int
    due_tomorrow: int
    overdue: int
    soft_launch_due: int
    active: int
    by_stage: dict[str, int]
    my_due_today: int
    my_overdue: int
    my_active: int
    open_change_requests: int
    as_of: UtcDatetime


class ChangesRequested(BaseModel):
    """What the client asked for — the record of why this project went back."""
    summary: str


class TransitionOut(BaseModel):
    id: int
    from_stage: Stage | None
    to_stage: Stage
    from_sub_status: str | None
    to_sub_status: str | None
    changed_by: int
    changed_by_name: str
    changed_at: UtcDatetime
    reason: str | None