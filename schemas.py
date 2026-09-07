"""Pydantic request/response models — the shapes the API sends and receives, kept separate from models.py's database shapes."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from models import Stage


class ProjectPoolItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rdr_number: str
    survey_name: str
    client_id: int
    created_at: datetime


class ProjectCreate(BaseModel):
    rdr_number: str
    survey_name: str
    client_id: int
    panel_criteria: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rdr_number: str
    survey_name: str
    client_id: int
    panel_criteria: str | None
    stage: Stage
    sub_status: str | None
    final_delivery_date: datetime | None
    final_delivery_date_locked: bool
    target: int | None
    created_by: int
    created_at: datetime
    updated_at: datetime
