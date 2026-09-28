from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.projects.schemas import Input

SourceType = Literal[
    "MEETING",
    "PDF",
    "WORD",
    "EXCEL",
    "CSV",
    "TEXT",
    "MARKDOWN",
    "EMAIL",
    "CHAT",
    "API_DOC",
    "UI",
    "BPMN",
    "REGULATION",
    "OTHER",
]
SourceStatus = Literal["ACTIVE", "SUPERSEDED", "ARCHIVED"]
Trust = Literal["HIGH", "MEDIUM", "LOW"]


class SourceCreate(Input):
    name: str = Field(min_length=1, max_length=200)
    source_type: SourceType = "OTHER"
    description: str = Field(default="", max_length=10000)
    owner: str = Field(default="", max_length=200)
    source_date: date | None = None
    trust_level: Trust = "LOW"


class SourceUpdate(Input):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    source_type: SourceType | None = None
    description: str | None = Field(default=None, max_length=10000)
    owner: str | None = Field(default=None, max_length=200)
    source_date: date | None = None
    trust_level: Trust | None = None
    status: SourceStatus | None = None
    supersedes_source_id: UUID | None = None


class SourceRead(SourceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    source_code: str
    status: SourceStatus
    supersedes_source_id: UUID | None
    revision: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class ParseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    source_version_id: UUID
    attempt_number: int
    parser_status: str
    parser_name: str
    parser_version: str
    parse_error: str | None
    metadata_json: dict
    created_at: datetime
    completed_at: datetime | None


class VersionRead(BaseModel):
    id: UUID
    project_id: UUID
    source_id: UUID
    version_number: int
    original_filename: str
    mime_type: str
    file_size: int
    checksum: str
    created_by: UUID
    created_at: datetime
    parser_status: str
    parser_name: str | None
    parser_version: str | None
    parse_error: str | None
    parse_run_id: UUID | None
    duplicate_version_ids: list[UUID]


class SectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    source_version_id: UUID
    parse_run_id: UUID
    ordinal: int
    text: str
    locator: dict
    display_reference: str
    cells: dict
