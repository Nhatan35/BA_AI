from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.errors import fail
from app.modules.audit.service import audit
from app.modules.auth.dependencies import DB
from app.modules.projects.authorization import Context
from app.modules.sources import repository as repo
from app.modules.sources import service
from app.modules.sources.models import ParsedSection, ParseRun, Source, SourceVersion
from app.modules.sources.schemas import (
    ParseRead,
    SectionRead,
    SourceCreate,
    SourceRead,
    SourceUpdate,
    VersionRead,
)

router = APIRouter(prefix="/projects/{project_id}/sources", tags=["sources"])


async def read_upload(file: UploadFile):
    try:
        content = await file.read(get_settings().upload_max_bytes + 1)
    finally:
        await file.close()
    return content


@router.post("", status_code=201)
async def upload(
    request: Request,
    context: Context,
    db: DB,
    file: Annotated[UploadFile, File()],
    metadata: Annotated[str, Form()] = "{}",
):
    repo.require_editor(db, context)
    if set((await request.form()).keys()) - {"file", "metadata"} or len(metadata) > 16384:
        fail(422, "INVALID_INPUT", "Upload fields are invalid.")
    try:
        body = SourceCreate.model_validate_json(metadata)
    except ValidationError:
        fail(422, "INVALID_INPUT", "Source metadata fields are invalid.")
    return await run_in_threadpool(
        service.upload,
        db,
        context,
        file.filename or "",
        file.content_type or "",
        await read_upload(file),
        metadata=body,
    )


@router.get("")
def sources(context: Context, db: DB, after: UUID | None = None, limit: int = Query(50, ge=1, le=100)):
    result = repo.page(db, context, Source, after, limit)
    result["items"] = [SourceRead.model_validate(row) for row in result["items"]]
    return result


@router.get("/{source_id}", response_model=SourceRead)
def detail(source_id: UUID, context: Context, db: DB):
    return repo.source(db, context, source_id)


@router.patch("/{source_id}", response_model=SourceRead)
def update(source_id: UUID, body: SourceUpdate, context: Context, db: DB):
    return service.update(db, context, source_id, body)


@router.post("/{source_id}/versions", status_code=201)
async def version_upload(
    request: Request, source_id: UUID, context: Context, db: DB, file: Annotated[UploadFile, File()]
):
    repo.require_editor(db, context)
    if set((await request.form()).keys()) - {"file"}:
        fail(422, "INVALID_INPUT", "Upload fields are invalid.")
    repo.source(db, context, source_id)
    return await run_in_threadpool(
        service.upload,
        db,
        context,
        file.filename or "",
        file.content_type or "",
        await read_upload(file),
        source_id=source_id,
    )


@router.get("/{source_id}/versions")
def versions(
    source_id: UUID, context: Context, db: DB, after: UUID | None = None, limit: int = Query(50, ge=1, le=100)
):
    repo.source(db, context, source_id)
    result = repo.page(db, context, SourceVersion, after, limit, source_id=source_id)
    result["items"] = [repo.version_read(db, context, row) for row in result["items"]]
    return result


@router.get("/{source_id}/versions/{version_id}", response_model=VersionRead)
def version(source_id: UUID, version_id: UUID, context: Context, db: DB):
    return repo.version_read(db, context, repo.scoped(db, context, SourceVersion, version_id, source_id))


@router.get("/{source_id}/versions/{version_id}/download")
def download(source_id: UUID, version_id: UUID, context: Context, db: DB):
    record = repo.scoped(db, context, SourceVersion, version_id, source_id)
    content = service.original(db, context, record)
    audit(db, context.user, context.project.id, "SOURCE_DOWNLOADED", "SourceVersion", record.id)
    db.commit()
    return Response(
        content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": (
                f"attachment; filename=source-{record.version_number}.bin; "
                f"filename*=UTF-8''{quote(record.original_filename, safe='')}"
            ),
            "Content-Security-Policy": "sandbox",
        },
    )


@router.post("/{source_id}/versions/{version_id}/reparse", response_model=ParseRead, status_code=201)
def reparse(source_id: UUID, version_id: UUID, context: Context, db: DB):
    return service.reparse(db, context, source_id, version_id)


@router.get("/{source_id}/versions/{version_id}/parses")
def parses(source_id: UUID, version_id: UUID, context: Context, db: DB):
    repo.scoped(db, context, SourceVersion, version_id, source_id)
    rows = db.scalars(
        select(ParseRun)
        .where(ParseRun.project_id == context.project.id, ParseRun.source_version_id == version_id)
        .order_by(ParseRun.attempt_number.desc())
        .limit(100)
    ).all()
    return {"items": [ParseRead.model_validate(row) for row in rows]}


@router.get("/{source_id}/versions/{version_id}/parsed")
def parsed(
    source_id: UUID,
    version_id: UUID,
    context: Context,
    db: DB,
    parse_run_id: UUID | None = None,
    after_ordinal: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    repo.scoped(db, context, SourceVersion, version_id, source_id)
    run = (
        repo.scoped(db, context, ParseRun, parse_run_id, source_id)
        if parse_run_id
        else repo.latest_parse(db, context, version_id)
    )
    if run is None or run.source_version_id != version_id:
        fail(404, "NOT_FOUND", "Parse was not found.")
    rows = db.scalars(
        select(ParsedSection)
        .where(
            ParsedSection.project_id == context.project.id,
            ParsedSection.parse_run_id == run.id,
            ParsedSection.ordinal > after_ordinal,
        )
        .order_by(ParsedSection.ordinal)
        .limit(limit + 1)
    ).all()
    return {
        "parse": ParseRead.model_validate(run),
        "items": [SectionRead.model_validate(row) for row in rows[:limit]],
        "next_ordinal": rows[limit - 1].ordinal if len(rows) > limit else None,
    }
