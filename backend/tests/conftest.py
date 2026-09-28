import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
runtime_url = os.getenv("TEST_DATABASE_URL")
owner_url = os.getenv("TEST_MIGRATION_DATABASE_URL")
if not runtime_url or not owner_url:
    raise pytest.UsageError(
        "NOT RUN: set TEST_DATABASE_URL and TEST_MIGRATION_DATABASE_URL for PostgreSQL tests"
    )
for url in (runtime_url, owner_url):
    parsed = make_url(url)
    if parsed.drivername != "postgresql+psycopg" or not parsed.database.endswith("_test"):
        raise pytest.UsageError("Tests require a dedicated PostgreSQL database ending in _test")
os.environ.update(
    DATABASE_URL=runtime_url,
    MIGRATION_DATABASE_URL=owner_url,
    APP_ENV="test",
    ALLOWED_ORIGINS='["http://testserver","http://localhost:3000"]',
    LOGIN_MAX_ATTEMPTS="1000",
    STORAGE_ROOT=str(Path(__file__).resolve().parents[2] / "var" / "test-storage"),
)

from app.core.database import get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.auth.models import User  # noqa: E402
from app.modules.auth.security import login_limiter, password_hasher  # noqa: E402
from scripts.grant_runtime import main as grant_runtime  # noqa: E402

PASSWORD = "Synthetic-foundation-password!"


@pytest.fixture(scope="session")
def owner_engine():
    engine = create_engine(owner_url, hide_parameters=True)
    command.upgrade(Config("alembic.ini"), "head")
    grant_runtime()
    yield engine
    get_engine().dispose()
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(owner_engine):
    with owner_engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE security_events, audit_logs, project_members, projects, "
                "auth_sessions, users CASCADE"
            )
        )
    login_limiter.buckets.clear()


@pytest.fixture
def provision(owner_engine):
    def create(email, status="ACTIVE", admin=False):
        with Session(owner_engine, expire_on_commit=False) as db, db.begin():
            user = User(
                email=email,
                display_name=email.split("@")[0],
                password_hash=password_hasher.hash(PASSWORD),
                status=status,
                is_system_admin=admin,
            )
            db.add(user)
            db.flush()
            return user

    return create


@pytest.fixture
def client(owner_engine):
    with TestClient(app, headers={"Origin": "http://testserver"}) as result:
        yield result


def sign_in(client, email):
    result = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert result.status_code == 200, result.text
    client.headers["x-csrf-token"] = result.json()["csrf_token"]
    return result


def create_project(client, name="Synthetic project"):
    result = client.post("/api/v1/projects", json={"name": name, "scope": "Synthetic BA scope"})
    assert result.status_code == 201, result.text
    return result.json()


@pytest.fixture
def world(provision, client):
    a = provision("a@example.com")
    b = provision("b@example.com")
    sign_in(client, a.email)
    project_a = create_project(client, "Project A — synthetic")
    sign_in(client, b.email)
    project_b = create_project(client, "Project B — synthetic")
    sign_in(client, a.email)
    return a, b, project_a, project_b
