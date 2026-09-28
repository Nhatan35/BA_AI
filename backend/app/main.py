import re
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from app.core.config import get_settings
from app.core.database import get_engine, verify_runtime_role
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.evidence.router import router as evidence_router
from app.modules.knowledge.router import router as knowledge_router
from app.modules.projects.router import router as project_router
from app.modules.sources.router import router as source_router


@asynccontextmanager
async def lifespan(app):
    verify_runtime_role()
    yield
    get_engine().dispose()


app = FastAPI(title="Medical BA AI", version="0.1.0", lifespan=lifespan, debug=False)
for router in (auth_router, project_router, audit_router, source_router, evidence_router, knowledge_router):
    app.include_router(router, prefix="/api/v1")


@app.middleware("http")
async def safe_response(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    is_upload = request.method == "POST" and re.fullmatch(
        r"/api/v1/projects/[^/]+/sources(?:/[^/]+/versions)?", request.url.path
    )
    maximum = get_settings().upload_max_bytes + 65536 if is_upload else 65536
    received = 0
    original_receive = request._receive

    async def bounded_receive():
        nonlocal received
        body = await original_receive()
        received += len(body.get("body", b""))
        if received > maximum:
            raise HTTPException(413, {"code": "BODY_TOO_LARGE", "message": "Request is too large."})
        return body

    request._receive = bounded_receive
    if (
        request.headers.get("content-length", "").isdigit()
        and int(request.headers["content-length"]) > maximum
    ):
        response = error_response(request, 413, "BODY_TOO_LARGE", "Request is too large.")
    else:
        response = await call_next(request)
        # FastAPI may normalize a receive exception to a body-parse 400.
        # Preserve the limit outcome for chunked requests with no Content-Length.
        if received > maximum:
            response = error_response(request, 413, "BODY_TOO_LARGE", "Request is too large.")
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def error_response(request, status, code, message):
    return JSONResponse(
        status_code=status,
        content={"code": code, "message": message, "request_id": getattr(request.state, "request_id", None)},
    )


@app.exception_handler(HTTPException)
async def http_error(request, error):
    detail = (
        error.detail
        if isinstance(error.detail, dict)
        else {"code": "REQUEST_FAILED", "message": str(error.detail)}
    )
    return error_response(request, error.status_code, detail["code"], detail["message"])


@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    # Do not echo Pydantic input values (which may contain submitted passwords).
    return error_response(request, 422, "INVALID_INPUT", "Request fields are invalid.")


@app.exception_handler(SQLAlchemyError)
async def database_error(request, error):
    return error_response(request, 503, "DATABASE_UNAVAILABLE", "The operation could not be completed.")


@app.exception_handler(Exception)
async def unexpected_error(request, error):
    return error_response(request, 500, "INTERNAL_ERROR", "The operation could not be completed.")


@app.get("/api/v1/health", tags=["health"])
def health():
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}
