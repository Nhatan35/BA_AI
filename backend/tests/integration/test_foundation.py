import json
import uuid
from datetime import timedelta

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_engine, set_actor, verify_runtime_role
from app.modules.audit.models import AuditLog, SecurityEvent
from app.modules.auth.models import AuthSession, User, now
from app.modules.auth.security import token_hash
from app.modules.projects.models import Project, ProjectMember
from scripts.grant_runtime import main as grant_runtime
from tests.conftest import PASSWORD, create_project, sign_in


def test_successful_authentication_and_no_password(provision, client, owner_engine):
    user = provision("person@example.com")
    response = sign_in(client, " PERSON@EXAMPLE.COM ")
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]
    assert response.json()["user"]["id"] == str(user.id)
    for path in ("/api/v1/auth/me", "/api/v1/projects"):
        payload = client.get(path).text
        assert "password" not in payload and PASSWORD not in payload
    with Session(owner_engine) as db:
        stored = db.get(User, user.id)
        assert stored.password_hash.startswith("$argon2id$") and stored.password_hash != PASSWORD
        session = db.scalar(select(AuthSession))
        cookie = client.cookies.get("medical_ba_session")
        assert session.token_hash == token_hash(cookie) and session.token_hash != cookie
        assert db.scalar(select(SecurityEvent.action)) == "LOGIN_SUCCEEDED"


@pytest.mark.parametrize("email,password", [("person@example.com", "wrong"), ("absent@example.com", "wrong")])
def test_failed_authentication_is_generic(email, password, provision, client):
    provision("person@example.com")
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"
    assert password not in response.text and email not in response.text
    assert not client.cookies.get("medical_ba_session")


def test_inactive_user_cannot_login(provision, client):
    provision("inactive@example.com", status="INACTIVE")
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "inactive@example.com", "password": PASSWORD}
        ).status_code
        == 401
    )


def test_logout_revokes_session(provision, client):
    provision("a@example.com")
    sign_in(client, "a@example.com")
    token = client.cookies.get("medical_ba_session")
    assert client.post("/api/v1/auth/logout").status_code == 204
    client.cookies.set("medical_ba_session", token)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_expired_and_inactivated_sessions(provision, client, owner_engine):
    user = provision("a@example.com")
    sign_in(client, user.email)
    with Session(owner_engine) as db, db.begin():
        db.scalar(select(AuthSession)).expires_at = now() - timedelta(seconds=1)
    assert client.get("/api/v1/projects").status_code == 401
    sign_in(client, user.email)
    with Session(owner_engine) as db, db.begin():
        db.get(User, user.id).status = "INACTIVE"
    assert client.get("/api/v1/projects").status_code == 401


def test_login_rotation_revokes_old_cookie(provision, client):
    provision("a@example.com")
    sign_in(client, "a@example.com")
    old = client.cookies.get("medical_ba_session")
    sign_in(client, "a@example.com")
    client.cookies.set("medical_ba_session", old)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_project_creation_and_audit(provision, client):
    user = provision("a@example.com")
    sign_in(client, user.email)
    project = create_project(client)
    assert project["my_role"] == "PROJECT_ADMIN"
    assert project["created_by"] == str(user.id)
    assert project["project_code"].startswith("PRJ-")
    assert project["project_code"][4:].isdigit()
    logs = client.get(f"/api/v1/projects/{project['id']}/audit").json()["items"]
    assert {row["action"] for row in logs} == {"PROJECT_CREATED", "MEMBERSHIP_CREATED"}
    assert all(row["project_id"] == project["id"] for row in logs)
    assert PASSWORD not in json.dumps(logs)


def test_project_list_only_active_memberships(world, client):
    _, _, a, b = world
    rows = client.get("/api/v1/projects").json()["items"]
    assert [row["id"] for row in rows] == [a["id"]]
    assert b["id"] not in json.dumps(rows)


def test_idor_project_members_and_identifier_guessing(world, client, owner_engine):
    _, _, a, b = world
    with Session(owner_engine) as db:
        member_b = db.scalar(select(ProjectMember).where(ProjectMember.project_id == uuid.UUID(b["id"])))
        member_id = str(member_b.id)
    for path in (
        f"/projects/{b['id']}",
        f"/projects/{b['id']}/members",
        f"/projects/{b['id']}/members/{member_id}",
        f"/projects/{b['id']}/audit",
        f"/projects/{a['id']}/members/{member_id}",
        f"/projects/{uuid.uuid4()}",
    ):
        response = client.get("/api/v1" + path)
        assert response.status_code == 404, response.text
        assert b["name"] not in response.text and member_id not in response.text
    response = client.patch(
        f"/api/v1/projects/{a['id']}/members/{member_id}",
        json={"role": "PROJECT_ADMIN", "status": "ACTIVE", "expected_revision": 1},
    )
    assert response.status_code == 404


@pytest.mark.parametrize("role", ["BA", "BUSINESS_OWNER", "MEDICAL_SME", "TECH", "QC", "VIEWER"])
def test_non_admin_roles_cannot_manage_members_or_settings(role, world, client):
    a_user, b_user, a, _ = world
    result = client.post(f"/api/v1/projects/{a['id']}/members", json={"email": b_user.email, "role": role})
    assert result.status_code == 201
    sign_in(client, b_user.email)
    assert client.get(f"/api/v1/projects/{a['id']}").status_code == 200
    assert (
        client.post(
            f"/api/v1/projects/{a['id']}/members", json={"email": a_user.email, "role": "VIEWER"}
        ).status_code
        == 403
    )
    update = {
        key: a[key] for key in ("name", "description", "organization", "scope", "out_of_scope", "status")
    }
    assert (
        client.patch(f"/api/v1/projects/{a['id']}", json={**update, "expected_revision": 1}).status_code
        == 403
    )
    assert client.get(f"/api/v1/projects/{a['id']}/audit").status_code == 403


def test_role_change_revocation_and_audit(world, client):
    _, b_user, a, _ = world
    base = f"/api/v1/projects/{a['id']}"
    member = client.post(base + "/members", json={"email": b_user.email, "role": "BA"}).json()
    changed = client.patch(
        base + "/members/" + member["id"], json={"role": "VIEWER", "status": "ACTIVE", "expected_revision": 1}
    )
    assert changed.status_code == 200 and changed.json()["revision"] == 2
    disabled = client.patch(
        base + "/members/" + member["id"],
        json={"role": "VIEWER", "status": "INACTIVE", "expected_revision": 2},
    )
    assert disabled.status_code == 200
    actions = {item["action"] for item in client.get(base + "/audit").json()["items"]}
    assert {"MEMBERSHIP_UPDATED", "PROJECT_ROLE_CHANGED"} <= actions
    sign_in(client, b_user.email)
    assert client.get(base).status_code == 404
    assert a["id"] not in [p["id"] for p in client.get("/api/v1/projects").json()["items"]]


def test_system_admin_does_not_bypass_membership(provision, client):
    provision("owner@example.com")
    provision("system@example.com", admin=True)
    sign_in(client, "owner@example.com")
    project = create_project(client)
    sign_in(client, "system@example.com")
    assert client.get(f"/api/v1/projects/{project['id']}").status_code == 404
    assert client.get("/api/v1/projects").json()["items"] == []


def test_self_role_escalation_and_lockout_denied(world, client):
    _, _, a, _ = world
    member = client.get(f"/api/v1/projects/{a['id']}/members").json()["items"][0]
    assert (
        client.patch(
            f"/api/v1/projects/{a['id']}/members/{member['id']}",
            json={"role": "BUSINESS_OWNER", "status": "ACTIVE", "expected_revision": 1},
        ).status_code
        == 409
    )


def test_csrf_origin_and_input_validation(provision, client):
    provision("a@example.com")
    sign_in(client, "a@example.com")
    assert (
        client.post("/api/v1/projects", json={"name": "x"}, headers={"x-csrf-token": "invalid"}).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/projects", json={"name": "x"}, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.post("/api/v1/projects", json={"name": "x", "created_by": str(uuid.uuid4())}).status_code
        == 422
    )
    assert client.post("/api/v1/projects", json={"name": " "}).status_code == 422
    response = client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": PASSWORD, "unexpected": "sensitive"}
    )
    assert response.status_code == 422 and PASSWORD not in response.text and "sensitive" not in response.text


def test_login_rate_control(provision, client):
    provision("a@example.com")
    settings = get_settings()
    original = settings.login_max_attempts
    settings.login_max_attempts = 2
    try:
        for _ in range(2):
            assert (
                client.post(
                    "/api/v1/auth/login", json={"email": "a@example.com", "password": "wrong"}
                ).status_code
                == 401
            )
        assert (
            client.post(
                "/api/v1/auth/login", json={"email": "a@example.com", "password": "wrong"}
            ).status_code
            == 429
        )
    finally:
        settings.login_max_attempts = original


def test_stale_and_stable_project_identity(world, client):
    _, _, a, _ = world
    body = {key: a[key] for key in ("name", "description", "organization", "scope", "out_of_scope", "status")}
    first = client.patch(
        f"/api/v1/projects/{a['id']}", json={**body, "name": "Updated", "expected_revision": 1}
    )
    assert first.status_code == 200 and first.json()["project_code"] == a["project_code"]
    assert (
        client.patch(f"/api/v1/projects/{a['id']}", json={**body, "expected_revision": 1}).status_code == 409
    )


def test_rls_missing_context_cross_project_and_pool_reuse(world):
    a_user, _, a, b = world
    verify_runtime_role()
    with Session(get_engine()) as db:
        assert db.scalars(select(Project)).all() == []
        set_actor(db, a_user.id)
        assert [str(p.id) for p in db.scalars(select(Project))] == [a["id"]]
        assert db.scalar(select(Project).where(Project.id == uuid.UUID(b["id"]))) is None
    with Session(get_engine()) as db:
        assert db.scalars(select(Project)).all() == []
        assert db.scalars(select(ProjectMember)).all() == []


def test_database_audit_mutation_and_member_move_rejected(world, owner_engine):
    _, _, a, b = world
    with owner_engine.begin() as conn:
        assert conn.execute(text("SELECT count(*) FROM audit_logs")).scalar() >= 4
    for query in ("UPDATE audit_logs SET action='tampered'", "DELETE FROM audit_logs"):
        with pytest.raises(DBAPIError), owner_engine.begin() as conn:
            conn.execute(text(query))
    with pytest.raises(DBAPIError), owner_engine.begin() as conn:
        conn.execute(
            text("UPDATE project_members SET project_id=:b WHERE project_id=:a"), {"a": a["id"], "b": b["id"]}
        )


def test_transaction_failure_rolls_back_project_and_membership(provision, client, monkeypatch, owner_engine):
    provision("a@example.com")
    sign_in(client, "a@example.com")
    from app.modules.projects import service

    def broken_audit(*args, **kwargs):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(service, "audit", broken_audit)
    with pytest.raises(RuntimeError, match="synthetic failure"):
        client.post("/api/v1/projects", json={"name": "rollback"})
    with Session(owner_engine) as db:
        assert db.scalars(select(Project)).all() == []
        assert db.scalars(select(ProjectMember)).all() == []
        assert db.scalars(select(AuditLog)).all() == []


def test_migrations_fresh_downgrade_upgrade(owner_engine):
    config = Config("alembic.ini")
    command.downgrade(config, "base")
    with owner_engine.connect() as conn:
        assert conn.execute(text("SELECT to_regclass('public.projects')")).scalar() is None
    command.upgrade(config, "head")
    grant_runtime()
    verify_runtime_role()
    with owner_engine.connect() as conn:
        assert (
            conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0004_ingestion_guards"
        )


def test_safe_bootstrap_and_provisioning(monkeypatch, owner_engine, capsys):
    import sys

    from app.cli import main

    monkeypatch.setattr("getpass.getpass", lambda prompt: PASSWORD)
    monkeypatch.setattr(
        sys,
        "argv",
        ["cli", "bootstrap-admin", "--email", "Admin@EXAMPLE.com", "--display-name", "Synthetic admin"],
    )
    main()
    with Session(owner_engine) as db:
        user = db.scalar(select(User))
        assert user.email == "admin@example.com" and user.is_system_admin
        assert db.scalars(select(ProjectMember)).all() == []
        assert db.scalar(select(SecurityEvent.action)) == "ADMIN_BOOTSTRAPPED"
    assert PASSWORD not in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main()
    monkeypatch.setattr(
        sys,
        "argv",
        ["cli", "create-user", "--email", "member@example.com", "--display-name", "Synthetic member"],
    )
    main()
    with Session(owner_engine) as db:
        member = db.scalar(select(User).where(User.email == "member@example.com"))
        assert member is not None and not member.is_system_admin


def test_rls_rejects_foreign_membership_write(world):
    a_user, _, _, b = world
    with Session(get_engine()) as db:
        set_actor(db, a_user.id)
        db.add(
            ProjectMember(
                project_id=uuid.UUID(b["id"]), user_id=a_user.id, role="PROJECT_ADMIN", created_by=a_user.id
            )
        )
        with pytest.raises(DBAPIError):
            db.flush()


def test_runtime_cannot_modify_audit_or_users(world):
    a_user, _, _, _ = world
    for query in (
        "UPDATE audit_logs SET action='tamper'",
        "DELETE FROM audit_logs",
        "UPDATE users SET is_system_admin=true",
    ):
        with Session(get_engine()) as db:
            set_actor(db, a_user.id)
            with pytest.raises(DBAPIError):
                db.execute(text(query))


def test_startup_rejects_owner_role_and_disabled_row_security(owner_engine, monkeypatch):
    import app.core.database as database

    with monkeypatch.context() as patch:
        patch.setattr(database, "get_engine", lambda: owner_engine)
        with pytest.raises(RuntimeError, match="must not own"):
            verify_runtime_role()
    with owner_engine.begin() as conn:
        conn.execute(text("ALTER TABLE projects DISABLE ROW LEVEL SECURITY"))
    try:
        with pytest.raises(RuntimeError, match="row policies"):
            verify_runtime_role()
    finally:
        with owner_engine.begin() as conn:
            conn.execute(text("ALTER TABLE projects ENABLE ROW LEVEL SECURITY"))


def test_common_errors_use_safe_consistent_shape(client):
    for response in (
        client.get("/api/v1/absent"),
        client.get("/api/v1/projects"),
        client.post("/api/v1/auth/login", json={"password": "x" * 70000}),
    ):
        assert response.status_code in {404, 401, 413}
        assert set(response.json()) == {"code", "message", "request_id"}
        assert response.json()["request_id"] == response.headers["x-request-id"]
        assert "password" not in response.text
