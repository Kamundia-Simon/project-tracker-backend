"""SQLAlchemy models for every table."""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship

from database import Base


class Stage(str, enum.Enum):
    PM_ASSIGNMENT = "PM_ASSIGNMENT"
    SCRIPTING = "SCRIPTING"
    QA = "QA"
    CLIENT_REVIEW = "CLIENT_REVIEW"
    QUOTAS = "QUOTAS"
    LIVE = "LIVE"
    DATA_PROCESSING = "DATA_PROCESSING"
    READY_FOR_DELIVERY = "READY_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    ON_HOLD = "ON_HOLD"


class MarketStatus(str, enum.Enum):
    PENDING = "PENDING"
    TRANSLATION = "TRANSLATION"
    QA = "QA"
    CLIENT_REVIEW = "CLIENT_REVIEW"
    APPROVED = "APPROVED"
    LIVE = "LIVE"
    DELIVERED = "DELIVERED"


class ChangeRequestStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    
    
class User(Base):
    """A person who can log in — PM, Scripter, QA, DP, or Viewer."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    clerk_user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/London")
    # Key into the frontend's preset avatar set, not an uploaded file.
    avatar: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_head_pm_override: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp())


class Role(Base):
    """A fixed job function (admin, pm, scripter, qa, dp, viewer) a user can hold on a project."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    # seed data, inserted once by the first migration: admin, pm, scripter, qa, dp, viewer
    
class UserRole(Base):
    """A user's baseline job function — distinct from per-project assignment in ProjectAssignment."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))


class Client(Base):
    """The company commissioning a survey."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)


class ProjectAssignment(Base):
    """Who currently holds which role on which project — closed out via unassigned_at, never deleted."""

    __tablename__ = "project_assignments"
    __table_args__ = (
        Index("ix_project_assignments_current", "project_id", "role_id", "unassigned_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp())
    unassigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Project(Base):
    """One survey project moving through the PM Assignment → ... → Delivered workflow."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    rdr_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    survey_name: Mapped[str] = mapped_column(String(255))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    client: Mapped["Client"] = relationship(lazy="joined")
    panel_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    survey_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    stage: Mapped[Stage] = mapped_column(Enum(Stage), index=True, default=Stage.PM_ASSIGNMENT)
    
    sub_status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # The scripter's one estimate covering scripting AND QA: when the client will have the link.
    client_link_eta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    final_delivery_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    final_delivery_date_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    target: Mapped[int | None] = mapped_column(nullable=True)
    soft_launch_target: Mapped[int | None] = mapped_column(nullable=True)
    live_start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expected_field_end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    scripting_checklist_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    qa_checklist_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    quota_checklist_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    final_qa_checklist_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    merged_delivery_required: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
        
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp(), onupdate=func.utc_timestamp())


class StageTransition(Base):
    """One immutable record of a project moving from one stage/sub-status to another — the project's timeline."""

    __tablename__ = "stage_transitions"
    __table_args__ = (
        Index("ix_stage_transitions_project_time", "project_id", "changed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    from_stage: Mapped[Stage | None] = mapped_column(Enum(Stage), nullable=True)
    to_stage: Mapped[Stage] = mapped_column(Enum(Stage))
    from_sub_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_sub_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp())
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class Revision(Base):
    """One round of client-requested changes during Client Review."""

    __tablename__ = "revisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    round_number: Mapped[int] = mapped_column()
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp())
    summary: Mapped[str] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Comment(Base):
    """A note left on a project by whoever's working on it."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp())


class Notification(Base):
    """An in-app alert for one user — assignment, rework, soft-launch due, etc."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp())


class FieldworkSnapshot(Base):
    """One point-in-time reading of a live project's completes/target, pulled from Cpi-Dashboard."""

    __tablename__ = "fieldwork_snapshots"
    __table_args__ = (
        Index("ix_fieldwork_snapshots_project_time", "project_id", "captured_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    captured_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp())
    completes: Mapped[int] = mapped_column()
    target: Mapped[int] = mapped_column()
    percent_complete: Mapped[Decimal] = mapped_column(Numeric(5, 1))
    ir: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)


class AuditLog(Base):
    """An immutable record of any change not already covered by StageTransition — date edits, reassignments, overrides."""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_project_time", "project_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    field_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp())
    
class ProjectMarket(Base):
    """One country on a multi-country survey — a tracking record with its own dates, not a workflow of its own."""

    __tablename__ = "project_markets"
    __table_args__ = (
        UniqueConstraint("project_id", "country", name="uq_project_markets_project_country"),
        Index("ix_project_markets_project_status", "project_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    country: Mapped[str] = mapped_column(String(64))
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[MarketStatus] = mapped_column(Enum(MarketStatus), default=MarketStatus.PENDING)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    live_start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp(), onupdate=func.utc_timestamp())


class ChangeRequest(Base):
    """A post-delivery ask against a finished project — tracked beside the stage machinery, never inside it."""

    __tablename__ = "change_requests"
    __table_args__ = (
        Index("ix_change_requests_project_status", "project_id", "status"),
        Index("ix_change_requests_assigned_status", "assigned_to", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    raised_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ChangeRequestStatus] = mapped_column(
        Enum(ChangeRequestStatus), default=ChangeRequestStatus.OPEN, nullable=False
    )
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.utc_timestamp(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)