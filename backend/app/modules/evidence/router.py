from uuid import UUID

from fastapi import APIRouter, Query

from app.modules.auth.dependencies import DB
from app.modules.evidence import service
from app.modules.evidence.models import Evidence
from app.modules.evidence.schemas import Confirmation, EvidenceCreate, EvidenceRead, EvidenceUpdate
from app.modules.projects.authorization import Context
from app.modules.sources import repository as repo

router = APIRouter(prefix="/projects/{project_id}/evidence", tags=["evidence"])


@router.post("", response_model=EvidenceRead, status_code=201)
def create(body: EvidenceCreate, context: Context, db: DB):
    return service.create(db, context, body)


@router.get("")
def evidence(
    context: Context,
    db: DB,
    source_id: UUID | None = None,
    after: UUID | None = None,
    limit: int = Query(50, ge=1, le=100),
):
    result = repo.page(db, context, Evidence, after, limit, source_id=source_id)
    result["items"] = [EvidenceRead.model_validate(row) for row in result["items"]]
    return result


@router.get("/{evidence_id}", response_model=EvidenceRead)
def detail(evidence_id: UUID, context: Context, db: DB):
    return repo.scoped(db, context, Evidence, evidence_id)


@router.patch("/{evidence_id}", response_model=EvidenceRead)
def update(evidence_id: UUID, body: EvidenceUpdate, context: Context, db: DB):
    return service.update(db, context, evidence_id, body)


@router.post("/{evidence_id}/confirmation", response_model=EvidenceRead)
def confirm(evidence_id: UUID, body: Confirmation, context: Context, db: DB):
    return service.confirm(db, context, evidence_id, body)
