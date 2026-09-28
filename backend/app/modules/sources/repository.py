from sqlalchemy import select, text

from app.core.database import set_actor
from app.core.errors import fail
from app.modules.projects import repository as projects
from app.modules.sources.models import ParseRun, Source, SourceVersion


def scoped(db, context, model, identifier, source_id=None, lock=False):
    query = select(model).where(model.project_id == context.project.id, model.id == identifier)
    if source_id is not None:
        query = query.where(model.source_id == source_id)
    if lock:
        query = query.with_for_update()
    result = db.scalar(query.execution_options(populate_existing=True))
    if result is None:
        fail(404, "NOT_FOUND", "Record was not found.")
    return result


def require_editor(db, context):
    # Recheck live membership after locks/commits, including mid-parse revocation.
    set_actor(db, context.user.id)
    member = projects.membership(db, context.project.id, context.user.id)
    if member is None:
        fail(404, "NOT_FOUND", "Project was not found.")
    if member.role not in {"PROJECT_ADMIN", "BA"}:
        fail(403, "FORBIDDEN", "BA or project administrator permission is required.")


def serialize_project_write(db, context):
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"ingestion:{context.project.id}"},
    )
    require_editor(db, context)


def latest_parse(db, context, version_id, successful=False):
    query = select(ParseRun).where(
        ParseRun.project_id == context.project.id, ParseRun.source_version_id == version_id
    )
    if successful:
        query = query.where(ParseRun.parser_status == "PARSED")
    return db.scalar(query.order_by(ParseRun.attempt_number.desc()).limit(1))


def version_read(db, context, version):
    from app.modules.sources.schemas import VersionRead

    run = latest_parse(db, context, version.id)
    duplicates = db.scalars(
        select(SourceVersion.id)
        .where(
            SourceVersion.project_id == context.project.id,
            SourceVersion.checksum == version.checksum,
            SourceVersion.id != version.id,
        )
        .order_by(SourceVersion.created_at)
        .limit(20)
    ).all()
    return VersionRead(
        **{
            key: getattr(version, key)
            for key in (
                "id",
                "project_id",
                "source_id",
                "version_number",
                "original_filename",
                "mime_type",
                "file_size",
                "checksum",
                "created_by",
                "created_at",
            )
        },
        parser_status=run.parser_status if run else "PENDING",
        parser_name=run.parser_name if run else None,
        parser_version=run.parser_version if run else None,
        parse_error=run.parse_error if run else None,
        parse_run_id=run.id if run else None,
        duplicate_version_ids=duplicates,
    )


def page(db, context, model, after, limit, **filters):
    query = select(model).where(model.project_id == context.project.id)
    for key, value in filters.items():
        if value is not None:
            query = query.where(getattr(model, key) == value)
    if after:
        query = query.where(model.id > after)
    rows = db.scalars(query.order_by(model.id).limit(limit + 1)).all()
    return {"items": rows[:limit], "next_cursor": rows[limit - 1].id if len(rows) > limit else None}


def source(db, context, source_id, lock=False):
    return scoped(db, context, Source, source_id, lock=lock)
