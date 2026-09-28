from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import AuthSession, User, now
from app.modules.auth.security import token_hash


def find_user(db: Session, email: str):
    return db.scalar(select(User).where(User.email == email))


def find_session(db: Session, token: str):
    return db.scalar(
        select(AuthSession)
        .join(User)
        .where(
            AuthSession.token_hash == token_hash(token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now(),
            User.status == "ACTIVE",
        )
    )
