"""SQLAlchemy models for every Phase 1 table — see docs/architecture.md §8 for the schema this implements."""

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
)
from sqlalchemy.orm import Mapped, mapped_column

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


class User(Base):
    """A person who can log in — PM, Scripter, QA, DP, or Viewer."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    clerk_user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/London")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_head_pm_override: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


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
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    unassigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Project(Base):
    """One survey project moving through the PM Assignment → ... → Delivered workflow."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    rdr_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    survey_name: Mapped[str] = mapped_column(String(255))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    panel_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)

    stage: Mapped[Stage] = mapped_column(Enum(Stage), index=True, default=Stage.PM_ASSIGNMENT)
    sub_status: Mapped[str | None] = mapped_column(String(32), nullable=True)

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

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


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
    changed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class Revision(Base):
    """One round of client-requested changes during Client Review."""

    __tablename__ = "revisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    round_number: Mapped[int] = mapped_column()
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    summary: Mapped[str] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Comment(Base):
    """A note left on a project by whoever's working on it."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


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
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FieldworkSnapshot(Base):
    """One point-in-time reading of a live project's completes/target, pulled from Cpi-Dashboard."""

    __tablename__ = "fieldwork_snapshots"
    __table_args__ = (
        Index("ix_fieldwork_snapshots_project_time", "project_id", "captured_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    captured_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
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
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
