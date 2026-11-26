#!/usr/bin/env python3
"""
scripts/create_admin.py
Create (or reset the password of) a SuperAdmin account.

Usage:
    python scripts/create_admin.py            # prompts for username/password
    ADMIN_USERNAME=... ADMIN_PASSWORD=... python scripts/create_admin.py
    python scripts/create_admin.py --reset    # change an existing user's password

No credentials are stored in this file.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _credentials import get_admin_credentials  # noqa: E402

MIN_PASSWORD_LENGTH = 8


ROLES = ("SuperAdmin", "Analyst", "Viewer")


def create_admin(username: str, password: str, reset: bool = False,
                 full_name: str = "Administrator", role: str = "SuperAdmin") -> str:
    """Create a user (SuperAdmin by default). Returns 'created', 'reset' or 'exists'."""
    if role not in ROLES:
        raise ValueError(f"Role must be one of {', '.join(ROLES)}.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")

    from backend.database import Base, SessionLocal, engine
    from backend.models.models import AdminUser
    from backend.routes.auth import pwd_context

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if user:
            if not reset:
                return "exists"
            user.password_hash = pwd_context.hash(password)
            db.commit()
            return "reset"
        db.add(AdminUser(
            username=username,
            password_hash=pwd_context.hash(password),
            full_name=full_name,
            role=role,
        ))
        db.commit()
        return "created"
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a SuperAdmin account.")
    parser.add_argument("--reset", action="store_true",
                        help="reset the password if the user already exists")
    args = parser.parse_args()

    creds = get_admin_credentials()
    if creds is None:
        print("No credentials: set ADMIN_USERNAME and ADMIN_PASSWORD, "
              "or run this in a terminal to be prompted.", file=sys.stderr)
        return 1

    username, password = creds
    try:
        result = create_admin(username, password, reset=args.reset)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    messages = {
        "created": f"Created admin user '{username}'.",
        "reset": f"Password reset for '{username}'.",
        "exists": f"User '{username}' already exists (use --reset to change the password).",
    }
    print(messages[result])
    return 0


if __name__ == "__main__":
    sys.exit(main())
