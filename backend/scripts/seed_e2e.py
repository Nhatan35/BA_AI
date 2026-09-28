"""Synthetic browser fixtures; refuses any database not explicitly named *_test."""

import json
import os
import secrets
import uuid
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend/.env")
owner_url = os.environ["TEST_MIGRATION_DATABASE_URL"]
if not make_url(owner_url).database.endswith("_test"):
    raise RuntimeError("Synthetic browser seed requires the dedicated test database")

from app.modules.audit.models import AuditLog  # noqa: E402
from app.modules.auth.models import User  # noqa: E402
from app.modules.auth.security import password_hasher  # noqa: E402
from app.modules.projects.models import Project, ProjectMember  # noqa: E402

suffix = uuid.uuid4().hex[:10]
fixtures = {}
with Session(create_engine(owner_url, hide_parameters=True)) as db, db.begin():
    for kind in ("owner", "member", "outsider"):
        password = secrets.token_urlsafe(24)
        email = f"{kind}.{suffix}@example.com"
        user = User(
            email=email, display_name="Synthetic " + kind, password_hash=password_hasher.hash(password)
        )
        db.add(user)
        db.flush()
        fixtures[kind] = {"email": email, "password": password, "id": str(user.id)}
    project = Project(
        project_code="PRJ-E2E-" + suffix,
        name="Private synthetic project",
        created_by=uuid.UUID(fixtures["outsider"]["id"]),
    )
    db.add(project)
    db.flush()
    member = ProjectMember(
        project_id=project.id, user_id=project.created_by, role="PROJECT_ADMIN", created_by=project.created_by
    )
    db.add(member)
    db.flush()
    db.add(
        AuditLog(
            project_id=project.id,
            actor_user_id=project.created_by,
            action="PROJECT_CREATED",
            entity_type="Project",
            entity_id=project.id,
        )
    )
    fixtures["private_project_id"] = str(project.id)
    fixtures["private_member_id"] = str(member.id)
(ROOT / "var").mkdir(exist_ok=True)
(ROOT / "var/e2e-fixtures.json").write_text(json.dumps(fixtures), encoding="utf-8")
print("Synthetic E2E fixtures written to ignored var/e2e-fixtures.json; credentials were not printed.")
