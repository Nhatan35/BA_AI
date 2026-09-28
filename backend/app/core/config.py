from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    migration_database_url: str | None = None
    app_env: Literal["development", "test", "production"] = "development"
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    session_hours: int = Field(default=8, ge=1, le=168)
    cookie_secure: bool = False
    login_max_attempts: int = Field(default=10, ge=1)
    login_window_seconds: int = Field(default=300, ge=1)
    # TECHNICAL DEFAULT — CONFIGURABLE, not a business policy.
    storage_root: Path = Path(__file__).resolve().parents[3] / "var" / "storage"
    upload_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1, le=100 * 1024 * 1024)
    csv_max_rows: int = Field(default=10000, ge=1)
    spreadsheet_max_sheets: int = Field(default=20, ge=1)
    spreadsheet_max_rows: int = Field(default=10000, ge=1)
    spreadsheet_max_columns: int = Field(default=256, ge=1, le=16384)
    parse_max_characters: int = Field(default=2_000_000, ge=1)
    parse_max_sections: int = Field(default=50000, ge=1)
    parse_max_pages: int = Field(default=500, ge=1)
    parse_max_expanded_bytes: int = Field(default=50 * 1024 * 1024, ge=1)
    parse_timeout_seconds: int = Field(default=30, ge=1, le=300)
    parse_max_concurrent: int = Field(default=2, ge=1, le=16)

    @model_validator(mode="after")
    def secure_configuration(self):
        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("PostgreSQL with psycopg is required")
        if self.app_env == "production":
            if not self.cookie_secure or any(not o.startswith("https://") for o in self.allowed_origins):
                raise ValueError("Production requires secure cookies and explicit HTTPS origins")
        if not self.allowed_origins or "*" in self.allowed_origins:
            raise ValueError("Explicit browser origins are required")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
