import re
import unicodedata

from fastapi import APIRouter, Query
from sqlalchemy import select, text

from app.modules.auth.dependencies import DB
from app.modules.projects.authorization import Context
from app.modules.sources.models import ParsedSection, ParseRun, Source, SourceVersion

router = APIRouter(prefix="/projects/{project_id}/search", tags=["knowledge"])


def excerpt(content: str, query: str) -> str:
    tokens = re.findall(r"\w+", query.casefold())
    positions = [content.casefold().find(token) for token in tokens]
    start = max(0, min((i for i in positions if i >= 0), default=0) - 150)
    return (
        ("…" if start else "") + content[start : start + 1200] + ("…" if len(content) > start + 1200 else "")
    )


@router.get("")
def search(
    context: Context,
    db: DB,
    q: str = Query(min_length=1, max_length=200),
    include_inactive: bool = False,
    offset: int = Query(0, ge=0, le=10000),
    limit: int = Query(25, ge=1, le=100),
):
    # Latest SUCCESSFUL parse per immutable version; failed retries do not erase knowledge.
    latest = (
        select(ParseRun.source_version_id, ParseRun.id)
        .where(ParseRun.project_id == context.project.id, ParseRun.parser_status == "PARSED")
        .distinct(ParseRun.source_version_id)
        .order_by(ParseRun.source_version_id, ParseRun.attempt_number.desc())
        .subquery()
    )
    query = (
        select(ParsedSection, Source, SourceVersion)
        .join(
            Source, (Source.id == ParsedSection.source_id) & (Source.project_id == ParsedSection.project_id)
        )
        .join(
            SourceVersion,
            (SourceVersion.id == ParsedSection.source_version_id)
            & (SourceVersion.project_id == ParsedSection.project_id),
        )
        .join(latest, latest.c.id == ParsedSection.parse_run_id)
        .where(
            ParsedSection.project_id == context.project.id,
            Source.project_id == context.project.id,
            SourceVersion.project_id == context.project.id,
            text(
                "to_tsvector('simple'::regconfig, parsed_sections.search_text) "
                "@@ plainto_tsquery('simple'::regconfig, :search_query)"
            ),
        )
    )
    if not include_inactive:
        query = query.where(Source.status == "ACTIVE")
    rows = db.execute(
        query.order_by(Source.source_code, SourceVersion.version_number.desc(), ParsedSection.ordinal)
        .offset(offset)
        .limit(limit + 1),
        {"search_query": unicodedata.normalize("NFC", q.strip())},
    ).all()
    return {
        "items": [
            {
                "project_id": context.project.id,
                "source_id": source.id,
                "source_code": source.source_code,
                "source_name": source.name,
                "source_status": source.status,
                "source_version_id": version.id,
                "version_number": version.version_number,
                "original_filename": version.original_filename,
                "parse_run_id": section.parse_run_id,
                "excerpt": excerpt(section.text, q),
                "locator": section.locator,
                "exact_reference": section.display_reference,
            }
            for section, source, version in rows[:limit]
        ],
        "next_offset": offset + limit if len(rows) > limit else None,
        "policy": (
            "All versions; latest successful parse per version; "
            "active sources by default. Inclusion is not approval."
        ),
    }
