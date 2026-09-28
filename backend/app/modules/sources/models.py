import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    column,
    func,
    literal_column,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.auth.models import now

SOURCE_TYPES = (
    "'MEETING','PDF','WORD','EXCEL','CSV','TEXT','MARKDOWN',"
    "'EMAIL','CHAT','API_DOC','UI','BPMN','REGULATION','OTHER'"
)


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("project_id", "id", name="uq_sources_project_id"),
        UniqueConstraint("project_id", "source_code", name="uq_sources_code"),
        ForeignKeyConstraint(
            ["project_id", "supersedes_source_id"], ["sources.project_id", "sources.id"], ondelete="RESTRICT"
        ),
        CheckConstraint(f"source_type IN ({SOURCE_TYPES})", name="ck_sources_type"),
        CheckConstraint("status IN ('ACTIVE','SUPERSEDED','ARCHIVED')", name="ck_sources_status"),
        CheckConstraint("trust_level IN ('HIGH','MEDIUM','LOW')", name="ck_sources_trust"),
        CheckConstraint(
            "supersedes_source_id IS NULL OR supersedes_source_id <> id", name="ck_sources_supersedes"
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"), index=True)
    source_code: Mapped[str] = mapped_column(String(40))
    source_type: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str] = mapped_column(String(200), default="")
    source_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    trust_level: Mapped[str] = mapped_column(String(10), default="LOW")
    supersedes_source_id: Mapped[uuid.UUID | None]
    revision: Mapped[int] = mapped_column(default=1)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class SourceVersion(Base):
    __tablename__ = "source_versions"
    __table_args__ = (
        UniqueConstraint("project_id", "source_id", "id", name="uq_versions_scope"),
        UniqueConstraint("project_id", "source_id", "version_number", name="uq_versions_number"),
        ForeignKeyConstraint(
            ["project_id", "source_id"], ["sources.project_id", "sources.id"], ondelete="RESTRICT"
        ),
        CheckConstraint("version_number > 0 AND file_size > 0", name="ck_versions_sizes"),
        CheckConstraint(
            "storage_key = project_id::text || '/' || source_id::text || '/' || id::text || '.bin'",
            name="ck_versions_key",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"), index=True)
    source_id: Mapped[uuid.UUID]
    version_number: Mapped[int]
    original_filename: Mapped[str] = mapped_column(String(240))
    storage_key: Mapped[str] = mapped_column(String(200), unique=True)
    mime_type: Mapped[str] = mapped_column(String(120))
    file_size: Mapped[int]
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ParseRun(Base):
    __tablename__ = "parse_runs"
    __table_args__ = (
        UniqueConstraint("project_id", "source_id", "source_version_id", "id", name="uq_parse_scope"),
        UniqueConstraint("source_version_id", "attempt_number", name="uq_parse_attempt"),
        CheckConstraint("attempt_number > 0", name="ck_parse_attempt"),
        ForeignKeyConstraint(
            ["project_id", "source_id", "source_version_id"],
            ["source_versions.project_id", "source_versions.source_id", "source_versions.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "parser_status IN ('PENDING','PROCESSING','PARSED','FAILED',"
            "'UNSUPPORTED','UNSUPPORTED_OR_OCR_REQUIRED')",
            name="ck_parse_status",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"), index=True)
    source_id: Mapped[uuid.UUID]
    source_version_id: Mapped[uuid.UUID]
    attempt_number: Mapped[int]
    parser_status: Mapped[str] = mapped_column(String(40), default="PENDING")
    parser_name: Mapped[str] = mapped_column(String(80))
    parser_version: Mapped[str] = mapped_column(String(40))
    parse_error: Mapped[str | None] = mapped_column(String(200))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ParsedSection(Base):
    __tablename__ = "parsed_sections"
    __table_args__ = (
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
        UniqueConstraint("parse_run_id", "ordinal", name="uq_sections_ordinal"),
        CheckConstraint("ordinal > 0", name="ck_sections_ordinal"),
        Index(
            "ix_sections_fts",
            func.to_tsvector(literal_column("'simple'::regconfig"), column("search_text")),
            postgresql_using="gin",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="RESTRICT"), index=True)
    source_id: Mapped[uuid.UUID]
    source_version_id: Mapped[uuid.UUID]
    parse_run_id: Mapped[uuid.UUID]
    ordinal: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    search_text: Mapped[str] = mapped_column(Text)
    locator: Mapped[dict] = mapped_column(JSONB)
    display_reference: Mapped[str] = mapped_column(String(500))
    cells: Mapped[dict] = mapped_column(JSONB, default=dict)
