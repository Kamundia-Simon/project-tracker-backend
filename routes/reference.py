"""Fixed vocabulary lists served by the API for reference purposes for Survey."""
from fastapi import APIRouter, Depends

from fastapi import HTTPException

from constants import CHECKLISTS, SURVEY_TYPES
from dependencies import get_current_user
from models import User

router = APIRouter(prefix="/api/reference", tags=["Reference"])


@router.get("/survey-types", response_model=list[str])
def list_survey_types(user: User = Depends(get_current_user)):
    """The ten survey types a project can be tagged with."""
    return list(SURVEY_TYPES)


@router.get("/checklists/{name}")
def get_checklist(name: str, user: User = Depends(get_current_user)):
    """A stage's checklist. Labels live here so the frontend never keeps its own copy."""
    if name not in CHECKLISTS:
        raise HTTPException(404, f"No checklist called {name}")
    return [
        {
            "section": section["section"],
            # derived items are ticked by the app; the UI shows them read-only.
            "derived": bool(section.get("derived")),
            "items": [{"id": item_id, "label": label} for item_id, label in section["items"]],
        }
        for section in CHECKLISTS[name]
    ]