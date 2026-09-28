from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.projects.schemas import Input

Classification = Literal[
    "FACT", "ASSUMPTION", "QUESTION", "DECISION", "RECOMMENDATION", "RISK", "ACTION_ITEM"
]


class Locator(Input):
    kind: Literal["LINE", "PDF_PAGE", "DOCX_PARAGRAPH", "DOCX_TABLE", "CSV", "XLSX"]
    start: int = Field(ge=1, le=50000)
    end: int | None = Field(default=None, ge=1, le=50000)
    sheet: str | None = Field(default=None, max_length=31)
    table: int | None = Field(default=None, ge=1)
    heading: str | None = Field(default=None, max_length=200)
    column_start: str | None = Field(default=None, pattern=r"^[A-Z]{1,3}$")
    column_end: str | None = Field(default=None, pattern=r"^[A-Z]{1,3}$")

    @model_validator(mode="after")
    def valid_range(self):
        if self.end is not None and self.end < self.start:
            raise ValueError("Invalid range")
        if self.kind == "XLSX" and not self.sheet:
            raise ValueError("Sheet required")
        if self.kind == "DOCX_TABLE" and self.table is None:
            raise ValueError("Table required")
        if self.kind in {"CSV", "XLSX"} and (not self.column_start or not self.column_end):
            raise ValueError("Columns required")
        return self


class EvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: UUID
    source_version_id: UUID
    parse_run_id: UUID | None = None
    locator: Locator
    extracted_text: str | None = Field(default=None, min_length=1, max_length=30000)
    summary: str = Field(default="", max_length=10000)
    classification: Classification
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_type: str = Field(default="MANUAL_EXTRACT", min_length=1, max_length=40)


class EvidenceUpdate(Input):
    expected_revision: int = Field(ge=1)
    summary: str | None = Field(default=None, max_length=10000)
    classification: Classification | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_type: str | None = Field(default=None, min_length=1, max_length=40)


class Confirmation(Input):
    expected_revision: int = Field(ge=1)
    confirmed: bool


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    source_id: UUID
    source_version_id: UUID
    parse_run_id: UUID
    evidence_code: str
    evidence_type: str
    locator: dict
    exact_reference: str
    extracted_text: str
    summary: str
    classification: Classification
    confidence: float | None
    confirmed_by: UUID | None
    confirmed_at: datetime | None
    revision: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime
