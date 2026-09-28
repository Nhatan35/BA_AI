"""Operator-only commands. Passwords are prompted; never accepted on the command line."""

import argparse
import getpass

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.audit.service import security_event
from app.modules.auth.models import User
from app.modules.auth.security import password_hasher


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["bootstrap-admin", "create-user", "deactivate-user"])
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name")
    args = parser.parse_args()
    email = str(TypeAdapter(EmailStr).validate_python(args.email.strip().lower()))
    url = get_settings().migration_database_url
    if not url:
        parser.error("MIGRATION_DATABASE_URL is required for operator commands")
    engine = create_engine(url, hide_parameters=True)
    with Session(engine) as db, db.begin():
        # Serialize bootstrap/provisioning; no two first-admin races.
        db.execute(text("SELECT pg_advisory_xact_lock(7311001)"))
        existing = db.scalar(select(User).where(User.email == email))
        if args.command == "deactivate-user":
            if not existing:
                parser.error("Account not found")
            existing.status = "INACTIVE"
            security_event(db, "USER_DEACTIVATED", existing.id)
        else:
            if existing:
                parser.error("Account already exists")
            if args.command == "bootstrap-admin" and db.scalar(select(func.count()).select_from(User)):
                parser.error("Bootstrap is allowed only on an empty user registry")
            if args.command == "create-user" and not db.scalar(
                select(User.id).where(User.is_system_admin.is_(True), User.status == "ACTIVE")
            ):
                parser.error("Bootstrap an administrator first")
            if not args.display_name or not args.display_name.strip():
                parser.error("--display-name is required")
            password = getpass.getpass("Password (12–1024 characters): ")
            if not 12 <= len(password) <= 1024 or password != getpass.getpass("Confirm password: "):
                parser.error("Password length or confirmation is invalid")
            user = User(
                email=email,
                display_name=args.display_name.strip(),
                password_hash=password_hasher.hash(password),
                is_system_admin=args.command == "bootstrap-admin",
            )
            db.add(user)
            db.flush()
            security_event(db, "ADMIN_BOOTSTRAPPED" if user.is_system_admin else "USER_PROVISIONED", user.id)
    print("Account operation completed. No project membership or approval authority was granted.")
    engine.dispose()


if __name__ == "__main__":
    main()
