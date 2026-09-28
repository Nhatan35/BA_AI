from openpyxl.utils import column_index_from_string, get_column_letter
from sqlalchemy import Integer, func, select

from app.core.errors import fail
from app.modules.audit.service import audit
from app.modules.auth.models import now
from app.modules.evidence.models import Evidence
from app.modules.projects import repository as projects
from app.modules.sources import repository as repo
from app.modules.sources.models import ParsedSection, ParseRun, SourceVersion
from app.modules.sources.parsers import display_reference


def extract(db, context, run, locator):
    location = locator.model_dump(exclude_none=True)
    end = locator.end or locator.start
    query = select(ParsedSection).where(
        ParsedSection.project_id == context.project.id,
        ParsedSection.parse_run_id == run.id,
        ParsedSection.locator["kind"].astext == locator.kind,
        ParsedSection.locator["start"].astext.cast(Integer).between(locator.start, end),
    )
    for field in ("sheet", "table"):
        value = getattr(locator, field)
        if value is not None:
            query = query.where(ParsedSection.locator[field].astext == str(value))
    sections = db.scalars(query.order_by(ParsedSection.ordinal).limit(501)).all()
    if (
        not sections
        or len(sections) > 500
        or sections[0].locator["start"] != locator.start
        or sections[-1].locator["start"] != end
    ):
        fail(422, "INVALID_REFERENCE", "The exact reference does not identify an available passage.")
    if locator.kind.startswith("DOCX"):
        location["heading"] = sections[0].locator.get("heading", "")
    if locator.kind in {"CSV", "XLSX"}:
        start_col, end_col = (
            column_index_from_string(locator.column_start),
            column_index_from_string(locator.column_end),
        )
        if start_col > end_col or any(
            end_col > column_index_from_string(item.locator["column_end"]) for item in sections
        ):
            fail(422, "INVALID_REFERENCE", "The column range is outside the parsed content.")
        texts = [
            "\t".join(item.cells.get(get_column_letter(i), "") for i in range(start_col, end_col + 1))
            for item in sections
        ]
    else:
        texts = [item.text for item in sections]
    text = "\n".join(texts)
    if not text.strip() or len(text) > 30000:
        fail(422, "INVALID_REFERENCE", "Choose a smaller, nonempty passage.")
    return location, text


def create(db, context, body):
    repo.serialize_project_write(db, context)
    repo.source(db, context, body.source_id)
    version = repo.scoped(db, context, SourceVersion, body.source_version_id, body.source_id)
    run = (
        repo.scoped(db, context, ParseRun, body.parse_run_id, body.source_id)
        if body.parse_run_id
        else repo.latest_parse(db, context, version.id, successful=True)
    )
    if run is None or run.source_version_id != version.id or run.parser_status != "PARSED":
        fail(422, "PARSE_REQUIRED", "Select a successful parse of this source version.")
    location, selected = extract(db, context, run, body.locator)
    quote = body.extracted_text if body.extracted_text is not None else selected
    if not quote.strip() or quote not in selected:
        fail(422, "QUOTE_MISMATCH", "The extract must occur exactly in the selected passage.")
    number = (
        db.scalar(
            select(func.max(func.substr(Evidence.evidence_code, 5).cast(Integer))).where(
                Evidence.project_id == context.project.id
            )
        )
        or 0
    ) + 1
    evidence = Evidence(
        project_id=context.project.id,
        source_id=version.source_id,
        source_version_id=version.id,
        parse_run_id=run.id,
        evidence_code=f"EVD-{number:03d}",
        evidence_type=body.evidence_type,
        locator=location,
        exact_reference=display_reference(location),
        extracted_text=quote,
        summary=body.summary,
        classification=body.classification,
        confidence=body.confidence,
        created_by=context.user.id,
    )
    db.add(evidence)
    db.flush()
    audit(
        db,
        context.user,
        context.project.id,
        "EVIDENCE_CREATED",
        "Evidence",
        evidence.id,
        {"classification": evidence.classification},
    )
    db.commit()
    return evidence


def update(db, context, evidence_id, body):
    repo.require_editor(db, context)
    record = repo.scoped(db, context, Evidence, evidence_id, lock=True)
    if record.revision != body.expected_revision:
        fail(409, "STALE_REVISION", "Reload the evidence before editing it.")
    changes = body.model_dump(exclude_unset=True, exclude={"expected_revision"})
    if any(value is None for key, value in changes.items() if key != "confidence"):
        fail(422, "INVALID_INPUT", "Evidence metadata fields cannot be null.")
    for key, value in changes.items():
        setattr(record, key, value)
    record.confirmed_by = record.confirmed_at = None
    record.revision += 1
    audit(
        db,
        context.user,
        context.project.id,
        "EVIDENCE_UPDATED",
        "Evidence",
        record.id,
        {"revision": record.revision, "fields": sorted(changes), "confirmation_cleared": True},
    )
    db.commit()
    return record


def confirm(db, context, evidence_id, body):
    repo.scoped(db, context, Evidence, evidence_id)
    member = projects.membership(db, context.project.id, context.user.id)
    if member is None:
        fail(404, "NOT_FOUND", "Project was not found.")
    if member.role not in {"PROJECT_ADMIN", "BUSINESS_OWNER"}:
        fail(403, "FORBIDDEN", "Business owner or project administrator permission is required.")
    record = repo.scoped(db, context, Evidence, evidence_id, lock=True)
    if record.revision != body.expected_revision:
        fail(409, "STALE_REVISION", "Reload the evidence before confirming it.")
    record.confirmed_by = context.user.id if body.confirmed else None
    record.confirmed_at = now() if body.confirmed else None
    record.revision += 1
    audit(
        db,
        context.user,
        context.project.id,
        "EVIDENCE_CONFIRMED" if body.confirmed else "EVIDENCE_CONFIRMATION_REVOKED",
        "Evidence",
        record.id,
        {"revision": record.revision},
    )
    db.commit()
    return record
