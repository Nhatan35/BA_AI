import secrets
from datetime import timedelta

from app.core.config import get_settings
from app.core.errors import fail
from app.modules.audit.service import security_event
from app.modules.auth.models import AuthSession, now
from app.modules.auth.repository import find_session, find_user
from app.modules.auth.security import dummy_hash, password_hasher, token_hash


def login(db, body, previous_token):
    user = find_user(db, str(body.email))
    password = body.password.get_secret_value()
    valid = password_hasher.verify(password, user.password_hash if user else dummy_hash)
    if not valid or user is None or user.status != "ACTIVE":
        security_event(db, "LOGIN_FAILED")
        db.commit()
        fail(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
    old = find_session(db, previous_token) if previous_token else None
    if old:
        old.revoked_at = now()
    token = secrets.token_urlsafe(32)
    session = AuthSession(
        user_id=user.id,
        token_hash=token_hash(token),
        expires_at=now() + timedelta(hours=get_settings().session_hours),
    )
    db.add(session)
    security_event(db, "LOGIN_SUCCEEDED", user.id)
    db.commit()
    return user, session, token


def logout(db, identity):
    identity.session.revoked_at = now()
    security_event(db, "LOGOUT", identity.user.id)
    db.commit()
