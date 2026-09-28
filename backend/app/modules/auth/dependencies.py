import secrets
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db, set_actor
from app.core.errors import fail
from app.modules.auth.models import AuthSession, User
from app.modules.auth.repository import find_session
from app.modules.auth.security import csrf_token

DB = Annotated[Session, Depends(get_db)]
COOKIE_NAME = "medical_ba_session"


@dataclass
class Identity:
    user: User
    session: AuthSession
    token: str


def check_origin(request: Request):
    if request.headers.get("origin") not in get_settings().allowed_origins:
        fail(403, "ORIGIN_DENIED", "Request origin is not allowed.")


def authenticated(request: Request, db: DB) -> Identity:
    token = request.cookies.get(COOKIE_NAME, "")
    session = find_session(db, token) if len(token) <= 128 else None
    if session is None:
        fail(401, "UNAUTHENTICATED", "Sign in to continue.")
    user = db.get(User, session.user_id)
    set_actor(db, user.id)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        check_origin(request)
        if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), csrf_token(token)):
            fail(403, "CSRF_DENIED", "Refresh your session before retrying this action.")
    return Identity(user=user, session=session, token=token)


Current = Annotated[Identity, Depends(authenticated)]
