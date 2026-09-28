import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.auth.models import now


class Evidence(Base):
    __tablename__ = "evidence"
    __table_args__ = (
        UniqueConstraint("project_id", "id", name="uq_evidence_project_id"),
        UniqueConstraint("project_id", "evidence_code", name="uq_evidence_code"),
        ForeignKeyConstraint(
            ["project_id", "source_id", "source_version_id", "parse_run_id"],
            [
                "parse_runs.project_id",
                "parse_runs.source_id",
                "parse_runs.source_version_id",
                "parse_runs.id",
            ],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "classification IN ('FACT','ASSUMPTION','QUESTION','DECISION',"
            "'RECOMMENDATION','RISK','ACTION_ITEM')",
            name="ck_evidence_class",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="ck_evidence_confidence"
        ),
        CheckConstraint("(confirmed_by IS NULL) = (confirmed_at IS NULL)", name="ck_evidence_confirmation"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"), index=True)
    source_id: Mapped[uuid.UUID]
    source_version_id: Mapped[uuid.UUID]
    parse_run_id: Mapped[uuid.UUID]
    evidence_code: Mapped[str] = mapped_column(String(40))
    evidence_type: Mapped[str] = mapped_column(String(40), default="MANUAL_EXTRACT")
    locator: Mapped[dict] = mapped_column(JSONB)
    exact_reference: Mapped[str] = mapped_column(String(500))
    extracted_text: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, default="")
    classification: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float | None]
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(default=1)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
