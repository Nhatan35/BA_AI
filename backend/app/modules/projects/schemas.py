from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["PROJECT_ADMIN", "BA", "BUSINESS_OWNER", "MEDICAL_SME", "TECH", "QC", "VIEWER"]
ProjectStatus = Literal["PLANNING", "ACTIVE", "ON_HOLD", "CLOSED"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProjectCreate(Input):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    organization: str = Field(default="", max_length=200)
    scope: str = Field(default="", max_length=10000)
    out_of_scope: str = Field(default="", max_length=10000)


class ProjectUpdate(ProjectCreate):
    status: ProjectStatus
    expected_revision: int = Field(ge=1)


class MemberCreate(Input):
    email: EmailStr
    role: Role

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class MemberUpdate(Input):
    role: Role
    status: Literal["ACTIVE", "INACTIVE"]
    expected_revision: int = Field(ge=1)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_code: str
    name: str
    description: str
    organization: str
    status: ProjectStatus
    scope: str
    out_of_scope: str
    revision: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    my_role: Role


class MemberRead(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    email: str
    display_name: str
    role: Role
    status: str
    revision: int


class ProjectList(BaseModel):
    items: list[ProjectRead]
    next_cursor: UUID | None = None


class MemberList(BaseModel):
    items: list[MemberRead]
    next_cursor: UUID | None = None
