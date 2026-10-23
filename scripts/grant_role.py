"""Bootstrap CLI for granting a baseline role — the out-of-band path, since granting admin via the API requires admin."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import SessionLocal
from models import Role, User, UserRole


def main(email: str, role_name: str) -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if user is None:
            print(f"No user with email {email} — they must sign in once before roles can be granted.")
            return 1

        role = db.query(Role).filter(Role.name == role_name).first()
        if role is None:
            known = sorted(n for (n,) in db.query(Role.name).all())
            print(f"Unknown role '{role_name}'. Known roles: {', '.join(known)}")
            return 1

        already = (
            db.query(UserRole)
            .filter(UserRole.user_id == user.id, UserRole.role_id == role.id)
            .first()
        )
        if already:
            print(f"{user.email} already holds {role.name}.")
            return 0

        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()
        print(f"Granted {role.name} to {user.email}.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/grant_role.py <email> <role>")
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))