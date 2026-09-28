from fastapi import APIRouter, Depends, Request, Response

from app.core.config import get_settings
from app.modules.auth import service
from app.modules.auth.dependencies import COOKIE_NAME, DB, Current, check_origin
from app.modules.auth.schemas import LoginInput, SessionRead, UserRead
from app.modules.auth.security import csrf_token, login_limiter, token_hash

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=SessionRead, dependencies=[Depends(check_origin)])
def login(body: LoginInput, request: Request, response: Response, db: DB):
    settings = get_settings()
    ip = request.client.host if request.client else "unknown"
    # Both source IP and account buckets; reverse-proxy deployment must preserve trusted client IP.
    for key in (token_hash("ip:" + ip), token_hash("email:" + str(body.email))):
        login_limiter.check(key, settings.login_max_attempts, settings.login_window_seconds)
    user, session, token = service.login(db, body, request.cookies.get(COOKIE_NAME, ""))
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.session_hours * 3600,
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return SessionRead(
        user=UserRead.model_validate(user), csrf_token=csrf_token(token), expires_at=session.expires_at
    )


@router.get("/me", response_model=SessionRead)
def me(identity: Current, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return SessionRead(
        user=UserRead.model_validate(identity.user),
        csrf_token=csrf_token(identity.token),
        expires_at=identity.session.expires_at,
    )


@router.post("/logout", status_code=204)
def logout(identity: Current, db: DB, response: Response):
    service.logout(db, identity)
    response.delete_cookie(
        COOKIE_NAME, path="/", secure=get_settings().cookie_secure, httponly=True, samesite="strict"
    )
