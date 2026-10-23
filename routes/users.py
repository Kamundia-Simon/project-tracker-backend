"""User accounts and the baseline roles granted to them"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, require_global_role
from models import AuditLog, Role, User, UserRole
from schemas import RoleGrant, UserOut, UserUpdate

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=list[UserOut])
def list_users(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Everyone, with the roles they hold."""
    rows = (
        db.query(User, Role.name)
        .outerjoin(UserRole, UserRole.user_id == User.id)
        .outerjoin(Role, Role.id == UserRole.role_id)
        .order_by(User.name)
        .all()
    )

    by_id: dict[int, UserOut] = {}
    for row_user, role_name in rows:
        entry = by_id.get(row_user.id)
        if entry is None:
            entry = UserOut(
                id=row_user.id,
                email=row_user.email,
                name=row_user.name,
                is_active=row_user.is_active,
                is_head_pm_override=row_user.is_head_pm_override,
                roles=[],
            )
            by_id[row_user.id] = entry
        if role_name is not None:
            entry.roles.append(role_name)

    for entry in by_id.values():
        entry.roles.sort()
    return list(by_id.values())


@router.post("/{user_id}/roles", response_model=UserOut, status_code=201)
def grant_role(
    user_id: int,
    payload: RoleGrant,
    actor: User = Depends(require_global_role("admin")),
    db: Session = Depends(get_db),
):
    """Give a user a baseline job function."""
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(404, "User not found")

    role = db.query(Role).filter(Role.name == payload.role).first()
    if role is None:
        raise HTTPException(422, f"Unknown role: {payload.role}")

    existing = (
        db.query(UserRole)
        .filter(UserRole.user_id == user_id, UserRole.role_id == role.id)
        .first()
    )
    if existing:
        raise HTTPException(409, f"{target.name} already holds the {role.name} role")

    db.add(UserRole(user_id=user_id, role_id=role.id))
    db.add(
        AuditLog(
            user_id=actor.id,
            action="role_granted",
            field_name="user_roles",
            new_value=f"{target.email}:{role.name}",
        )
    )
    db.commit()
    return _user_out(db, target)


@router.delete("/{user_id}/roles/{role_name}", response_model=UserOut)
def revoke_role(
    user_id: int,
    role_name: str,
    actor: User = Depends(require_global_role("admin")),
    db: Session = Depends(get_db),
):
    """Remove a baseline job function. Project assignments already made are left untouched."""
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(404, "User not found")

    if user_id == actor.id and role_name == "admin":
        raise HTTPException(409, "You cannot revoke your own admin role")

    held = (
        db.query(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .filter(UserRole.user_id == user_id, Role.name == role_name)
        .first()
    )
    if held is None:
        raise HTTPException(404, f"{target.name} does not hold the {role_name} role")

    db.delete(held)
    db.add(
        AuditLog(
            user_id=actor.id,
            action="role_revoked",
            field_name="user_roles",
            old_value=f"{target.email}:{role_name}",
        )
    )
    db.commit()
    return _user_out(db, target)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    actor: User = Depends(require_global_role("admin")),
    db: Session = Depends(get_db),
):
    """Deactivate an account or grant the head-PM override."""
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(404, "User not found")

    if payload.is_active is False and user_id == actor.id:
        raise HTTPException(409, "You cannot deactivate your own account")

    for field, value in payload.model_dump(exclude_unset=True).items():
        old = getattr(target, field)
        setattr(target, field, value)
        db.add(
            AuditLog(
                user_id=actor.id,
                action="user_updated",
                field_name=field,
                old_value=str(old),
                new_value=str(value),
            )
        )

    db.commit()
    db.refresh(target)
    return _user_out(db, target)


def _user_out(db: Session, target: User) -> UserOut:
    roles = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == target.id)
        .all()
    )
    return UserOut(
        id=target.id,
        email=target.email,
        name=target.name,
        is_active=target.is_active,
        is_head_pm_override=target.is_head_pm_override,
        roles=sorted(name for (name,) in roles),
    )