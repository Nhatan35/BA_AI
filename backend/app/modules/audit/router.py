from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.modules.audit.models import AuditLog
from app.modules.auth.dependencies import DB
from app.modules.projects.authorization import Context

router = APIRouter(tags=["audit"])


class AuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    actor_user_id: UUID
    action: str
    entity_type: str
    entity_id: UUID
    timestamp: datetime
    safe_metadata: dict


class AuditList(BaseModel):
    items: list[AuditRead]
    next_cursor: UUID | None = None


@router.get("/projects/{project_id}/audit", response_model=AuditList)
def logs(context: Context, db: DB, after: UUID | None = None, limit: int = Query(50, ge=1, le=100)):
    context.require_admin()
    query = select(AuditLog).where(AuditLog.project_id == context.project.id)
    if after:
        query = query.where(AuditLog.id > after)
    rows = db.scalars(query.order_by(AuditLog.id).limit(limit + 1)).all()
    return AuditList(
        items=[AuditRead.model_validate(row) for row in rows[:limit]],
        next_cursor=rows[limit - 1].id if len(rows) > limit else None,
    )
