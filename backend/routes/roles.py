"""The fixed set of roles a user can hold."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import Role, User
from schemas import RoleOut

router = APIRouter(prefix="/api/roles", tags=["Roles"])


@router.get("", response_model=list[RoleOut])
def list_roles(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Seeded at migration time"""
    return db.query(Role).order_by(Role.name).all()