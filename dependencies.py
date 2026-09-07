"""FastAPI dependencies for Clerk authentication, local user sync, and the role checks."""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from auth import authenticate
from database import get_db
from models import ProjectAssignment, Role, User, UserRole


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Verify the Clerk token, then return the matching local users row, creating it on first login."""
    identity = authenticate(request)

    user = db.query(User).filter(User.clerk_user_id == identity["clerk_user_id"]).first()
    if user is None:
        user = User(
            clerk_user_id=identity["clerk_user_id"],
            email=identity["email"],
            name=identity["email"].split("@")[0],
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated")

    return user


def user_global_roles(db: Session, user: User) -> set[str]:
    """The user's baseline job functions, independent of any project."""
    rows = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    return {name for (name,) in rows}


def user_project_roles(db: Session, user: User, project_id: int) -> set[str]:
    """The roles this user currently holds on one specific project."""
    rows = (
        db.query(Role.name)
        .join(ProjectAssignment, ProjectAssignment.role_id == Role.id)
        .filter(
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.user_id == user.id,
            ProjectAssignment.unassigned_at.is_(None),
        )
        .all()
    )
    return {name for (name,) in rows}


def require_global_role(*allowed: str):
    """Dependency factory gating an endpoint to users holding one of the given baseline roles."""

    def check(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        held = user_global_roles(db, user)
        if "admin" in held or held & set(allowed):
            return user
        raise HTTPException(
            status_code=403,
            detail=f"This action requires one of: {', '.join(allowed)}",
        )

    return check