import hashlib
import uuid
from pathlib import Path

from sqlalchemy import Integer, func, select

from app.core.database import set_actor
from app.core.errors import fail
from app.modules.audit.service import audit
from app.modules.auth.models import now
from app.modules.sources import repository as repo
from app.modules.sources.models import ParsedSection, ParseRun, Source, SourceVersion
from app.modules.sources.parsers import isolated_parse, parser_identity, validate_upload
from app.modules.sources.schemas import SourceRead
from app.storage.local import get_storage, storage_key


def upload(db, context, filename, mime, content, metadata=None, source_id=None):
    repo.serialize_project_write(db, context)
    if source_id:
        source = repo.source(db, context, source_id, lock=True)
        if source.status != "ACTIVE":
            fail(409, "SOURCE_INACTIVE", "Activate the source before uploading another version.")
    else:
        number = (
            db.scalar(
                select(func.max(func.substr(Source.source_code, 5).cast(Integer))).where(
                    Source.project_id == context.project.id
                )
            )
            or 0
        ) + 1
        source = Source(
            id=uuid.uuid4(),
            project_id=context.project.id,
            source_code=f"SRC-{number:03d}",
            created_by=context.user.id,
            **metadata.model_dump(),
        )
        db.add(source)
        db.flush()
        audit(db, context.user, context.project.id, "SOURCE_CREATED", "Source", source.id)
    extension, canonical_mime = validate_upload(filename, mime, content)
    number = (
        db.scalar(
            select(func.max(SourceVersion.version_number)).where(
                SourceVersion.project_id == context.project.id, SourceVersion.source_id == source.id
            )
        )
        or 0
    ) + 1
    version_id = uuid.uuid4()
    key = storage_key(context.project.id, source.id, version_id)
    version = SourceVersion(
        id=version_id,
        project_id=context.project.id,
        source_id=source.id,
        version_number=number,
        original_filename=filename,
        mime_type=canonical_mime,
        file_size=len(content),
        checksum=hashlib.sha256(content).hexdigest(),
        storage_key=key,
        created_by=context.user.id,
    )
    storage = get_storage()
    try:
        storage.put(context.project.id, key, content)
    except OSError:
        fail(503, "STORAGE_UNAVAILABLE", "The original file could not be stored.")
    try:
        db.add(version)
        db.flush()
        audit(
            db,
            context.user,
            context.project.id,
            "SOURCE_VERSION_UPLOADED",
            "SourceVersion",
            version.id,
            {"version_number": number, "file_size": len(content)},
        )
        run = new_parse(db, context, version, extension)
        db.commit()
    except Exception:
        db.rollback()
        storage.discard_uncommitted(context.project.id, key)
        raise
    perform_parse(db, context, version, run, content, extension)
    set_actor(db, context.user.id)
    return {"source": SourceRead.model_validate(source), "version": repo.version_read(db, context, version)}


def new_parse(db, context, version, extension):
    name, parser_version = parser_identity(extension)
    number = (
        db.scalar(
            select(func.max(ParseRun.attempt_number)).where(
                ParseRun.project_id == context.project.id, ParseRun.source_version_id == version.id
            )
        )
        or 0
    ) + 1
    run = ParseRun(
        project_id=context.project.id,
        source_id=version.source_id,
        source_version_id=version.id,
        attempt_number=number,
        parser_name=name,
        parser_version=parser_version,
        created_by=context.user.id,
    )
    db.add(run)
    db.flush()
    audit(
        db,
        context.user,
        context.project.id,
        "PARSE_REQUESTED",
        "ParseRun",
        run.id,
        {"attempt_number": number},
    )
    return run


def perform_parse(db, context, version, run, content, extension):
    repo.require_editor(db, context)
    run.parser_status = "PROCESSING"
    audit(db, context.user, context.project.id, "PARSE_STARTED", "ParseRun", run.id)
    db.commit()
    result = isolated_parse(content, extension)
    repo.require_editor(db, context)
    for ordinal, section in enumerate(result.get("sections", []), 1):
        db.add(
            ParsedSection(
                project_id=context.project.id,
                source_id=version.source_id,
                source_version_id=version.id,
                parse_run_id=run.id,
                ordinal=ordinal,
                **section,
            )
        )
    db.flush()
    run.parser_status = result["status"]
    run.parse_error = result.get("error")
    run.metadata_json = result.get("metadata", {})
    run.completed_at = now()
    audit(
        db,
        context.user,
        context.project.id,
        "PARSE_COMPLETED" if run.parser_status == "PARSED" else "PARSE_FAILED",
        "ParseRun",
        run.id,
        {"status": run.parser_status, "error_code": run.parse_error},
    )
    db.commit()


def original(db, context, version):
    try:
        content = get_storage().read(context.project.id, version.storage_key)
    except (OSError, ValueError):
        fail(503, "STORAGE_UNAVAILABLE", "The original file is unavailable.")
    if len(content) != version.file_size or hashlib.sha256(content).hexdigest() != version.checksum:
        fail(503, "STORAGE_INTEGRITY_ERROR", "The original file failed its integrity check.")
    return content


def reparse(db, context, source_id, version_id):
    repo.serialize_project_write(db, context)
    repo.source(db, context, source_id)
    version = repo.scoped(db, context, SourceVersion, version_id, source_id)
    content = original(db, context, version)
    extension = Path(version.original_filename).suffix.lower()
    run = new_parse(db, context, version, extension)
    db.commit()
    perform_parse(db, context, version, run, content, extension)
    return run


def update(db, context, source_id, body):
    repo.serialize_project_write(db, context)
    source = repo.source(db, context, source_id, lock=True)
    if source.revision != body.expected_revision:
        fail(409, "STALE_REVISION", "Reload the source before editing it.")
    changes = body.model_dump(exclude_unset=True, exclude={"expected_revision"})
    if any(
        value is None for key, value in changes.items() if key not in {"source_date", "supersedes_source_id"}
    ):
        fail(422, "INVALID_INPUT", "Source metadata fields cannot be null.")
    replacement = changes.get("supersedes_source_id")
    if replacement:
        if replacement == source.id:
            fail(422, "INVALID_SUPERSESSION", "A source cannot supersede itself.")
        if source.supersedes_source_id or source.status != "ACTIVE":
            fail(
                409,
                "INVALID_SUPERSESSION",
                "Only an active source without an existing replacement link may supersede another source.",
            )
        prior = repo.source(db, context, replacement, lock=True)
        if prior.status != "ACTIVE" or prior.supersedes_source_id:
            fail(
                409,
                "INVALID_SUPERSESSION",
                "The replaced source must be active and have no replacement chain in this MVP.",
            )
        prior.status, prior.revision = "SUPERSEDED", prior.revision + 1
        audit(
            db,
            context.user,
            context.project.id,
            "SOURCE_SUPERSEDED",
            "Source",
            prior.id,
            {"replacement_id": str(source.id)},
        )
    elif "supersedes_source_id" in changes and source.supersedes_source_id:
        fail(409, "INVALID_SUPERSESSION", "An explicit replacement link cannot be removed.")
    for key, value in changes.items():
        setattr(source, key, value)
    source.revision += 1
    action = {
        "ARCHIVED": "SOURCE_ARCHIVED",
        "SUPERSEDED": "SOURCE_SUPERSEDED",
        "ACTIVE": "SOURCE_ACTIVATED",
    }.get(changes.get("status"), "SOURCE_METADATA_UPDATED")
    audit(
        db,
        context.user,
        context.project.id,
        action,
        "Source",
        source.id,
        {"revision": source.revision, "fields": sorted(changes)},
    )
    db.commit()
    return source
