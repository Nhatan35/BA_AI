import io
import subprocess
import uuid
import zipfile
from dataclasses import replace

import pytest
from alembic import command
from alembic.config import Config
from openpyxl import Workbook
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.database import get_engine, set_actor
from app.modules.projects.models import ProjectMember
from app.modules.sources.models import ParsedSection
from app.modules.sources.parsers import Limits, ParseFailure, StructuredParser, isolated_parse, parse_slots
from scripts.grant_runtime import main as grant_runtime
from tests.conftest import sign_in
from tests.fixtures import synthetic_files
from tests.integration.test_ingestion import evidence, upload


@pytest.mark.parametrize(
    "role", ["BA", "PROJECT_ADMIN", "BUSINESS_OWNER", "MEDICAL_SME", "TECH", "QC", "VIEWER"]
)
def test_source_and_evidence_role_matrix(role, world, client):
    a_user, b_user, a, _ = world
    data = upload(client, a).json()
    record = evidence(client, a, data).json()
    prefix = f"/api/v1/projects/{a['id']}"
    added = client.post(prefix + "/members", json={"email": b_user.email, "role": role})
    assert added.status_code == 201
    sign_in(client, b_user.email)
    base = prefix + f"/sources/{data['source']['id']}"
    version = base + f"/versions/{data['version']['id']}"
    for path in ("/sources", "/evidence", "/search?q=cancellation"):
        assert client.get(prefix + path).status_code == 200
    for path in (base, base + "/versions", version, version + "/download", version + "/parsed"):
        assert client.get(path).status_code == 200
    editor = role in {"BA", "PROJECT_ADMIN"}
    assert upload(client, a).status_code == (201 if editor else 403)
    assert upload(client, a, source=data["source"]["id"]).status_code == (201 if editor else 403)
    assert client.post(version + "/reparse").status_code == (201 if editor else 403)
    assert client.patch(base, json={"owner": "Synthetic BA", "expected_revision": 1}).status_code == (
        200 if editor else 403
    )
    assert evidence(client, a, data).status_code == (201 if editor else 403)
    updated = client.patch(
        prefix + f"/evidence/{record['id']}", json={"summary": "Synthetic summary", "expected_revision": 1}
    )
    assert updated.status_code == (200 if editor else 403)
    revision = 2 if editor else 1
    confirmed = client.post(
        prefix + f"/evidence/{record['id']}/confirmation",
        json={"expected_revision": revision, "confirmed": True},
    )
    assert confirmed.status_code == (200 if role in {"PROJECT_ADMIN", "BUSINESS_OWNER"} else 403)
    sign_in(client, a_user.email)
    member = added.json()
    assert (
        client.patch(
            prefix + f"/members/{member['id']}",
            json={"role": role, "status": "INACTIVE", "expected_revision": 1},
        ).status_code
        == 200
    )
    sign_in(client, b_user.email)
    for path in ("/sources", "/evidence", "/search?q=cancellation"):
        assert client.get(prefix + path).status_code == 404
    assert client.get(version + "/download").status_code == 404
    assert upload(client, a).status_code == 404


def test_exact_csv_xlsx_ranges_and_no_formula_execution(world, client):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Booking"
    for col, value in zip("ABCD", ["Synthetic", "Cancellation", "=1+1", "Unresolved"]):
        sheet[f"{col}12"] = value
    output = io.BytesIO()
    workbook.save(output)
    files = [
        (
            "range.xlsx",
            output.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        synthetic_files()["csv"],
    ]
    for file in files:
        data = upload(client, world[2], file).json()
        xlsx = file[0].endswith("xlsx")
        locator = {
            "kind": "XLSX" if xlsx else "CSV",
            "start": 12 if xlsx else 2,
            "column_start": "B",
            "column_end": "D" if xlsx else "B",
        }
        if xlsx:
            locator["sheet"] = "Booking"
        body = {
            "source_id": data["source"]["id"],
            "source_version_id": data["version"]["id"],
            "locator": locator,
            "classification": "FACT",
        }
        response = client.post(f"/api/v1/projects/{world[2]['id']}/evidence", json=body)
        assert response.status_code == 201, response.text
        assert response.json()["exact_reference"] == ("Booking!B12:D12" if xlsx else "CSV!B2:B2 (rows 2)")
        if xlsx:
            assert "=1+1" in response.json()["extracted_text"]
        locator["column_end"] = "Z"
        assert client.post(f"/api/v1/projects/{world[2]['id']}/evidence", json=body).status_code == 422


def test_explicit_supersession_and_stale_metadata(world, client):
    a = upload(client, world[2]).json()
    b = upload(client, world[2]).json()
    prefix = f"/api/v1/projects/{world[2]['id']}"
    replacement = client.patch(
        prefix + f"/sources/{b['source']['id']}",
        json={"supersedes_source_id": a["source"]["id"], "expected_revision": 1},
    )
    assert replacement.status_code == 200
    assert client.get(prefix + f"/sources/{a['source']['id']}").json()["status"] == "SUPERSEDED"
    assert len(client.get(prefix + "/search?q=cancellation").json()["items"]) == 3
    assert len(client.get(prefix + "/search?q=cancellation&include_inactive=true").json()["items"]) == 6
    assert (
        client.patch(
            prefix + f"/sources/{b['source']['id']}", json={"name": "Stale", "expected_revision": 1}
        ).status_code
        == 409
    )
    assert (
        client.patch(
            prefix + f"/sources/{b['source']['id']}",
            json={"supersedes_source_id": None, "expected_revision": 2},
        ).status_code
        == 409
    )


def test_database_rejects_late_parse_append(world, client):
    data = upload(client, world[2]).json()
    with Session(get_engine()) as db:
        set_actor(db, world[0].id)
        db.add(
            ParsedSection(
                project_id=uuid.UUID(world[2]["id"]),
                source_id=uuid.UUID(data["source"]["id"]),
                source_version_id=uuid.UUID(data["version"]["id"]),
                parse_run_id=uuid.UUID(data["version"]["parse_run_id"]),
                ordinal=4,
                text="Forged",
                search_text="Forged",
                locator={"kind": "LINE", "start": 4},
                display_reference="Line 4",
            )
        )
        with pytest.raises(DBAPIError):
            db.flush()


def test_revocation_during_parse_preserves_registered_original(world, client, owner_engine, monkeypatch):
    a_user, b_user, a, _ = world
    prefix = f"/api/v1/projects/{a['id']}"
    member = client.post(prefix + "/members", json={"email": b_user.email, "role": "BA"}).json()
    sign_in(client, b_user.email)

    def revoke(content, extension):
        with Session(owner_engine) as db, db.begin():
            db.get(ProjectMember, uuid.UUID(member["id"])).status = "INACTIVE"
        return {"status": "FAILED", "error": "SYNTHETIC_INTERRUPTION"}

    monkeypatch.setattr("app.modules.sources.service.isolated_parse", revoke)
    assert upload(client, a).status_code == 404
    sign_in(client, a_user.email)
    sources = client.get(prefix + "/sources").json()["items"]
    versions = client.get(prefix + f"/sources/{sources[0]['id']}/versions").json()["items"]
    assert versions[0]["parser_status"] == "PROCESSING"
    assert (
        client.get(prefix + f"/sources/{sources[0]['id']}/versions/{versions[0]['id']}/download").status_code
        == 200
    )


def test_worker_timeout_and_archive_xml_controls(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("synthetic worker", 1)

    monkeypatch.setattr("subprocess.run", timeout)
    assert isolated_parse(b"synthetic", ".txt") == {"status": "FAILED", "error": "PARSER_TIMEOUT"}
    for payload in (b'<!DOCTYPE x [<!ENTITY y SYSTEM "file:///private">]><x/>', b"<macroEnabled/>"):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as package:
            package.writestr("word/document.xml", payload)
        with pytest.raises(ParseFailure) as error:
            StructuredParser(".docx").parse(buffer.getvalue(), Limits.configured())
        assert error.value.status == "UNSUPPORTED"


def test_csv_unicode_multiline_and_xlsx_sheet_limit():
    parsed = StructuredParser(".csv").parse(
        'Name,Statement\r\n"Hủy lịch","first\nsecond"\r\n'.encode(), Limits.configured()
    )
    assert parsed["sections"][1]["cells"]["B"] == "first\nsecond"
    assert parsed["sections"][1]["locator"]["start"] == 2
    workbook = Workbook()
    workbook.create_sheet("Second")
    output = io.BytesIO()
    workbook.save(output)
    with pytest.raises(ParseFailure):
        StructuredParser(".xlsx").parse(
            output.getvalue(), replace(Limits.configured(), spreadsheet_max_sheets=1)
        )


def test_parser_capacity_control():
    slots = parse_slots()
    count = 0
    try:
        while slots.acquire(blocking=False):
            count += 1
        assert isolated_parse(b"synthetic", ".txt") == {"status": "FAILED", "error": "PARSER_CAPACITY_RETRY"}
    finally:
        for _ in range(count):
            slots.release()


def test_chunked_body_limit_without_content_length(client):
    response = client.post(
        "/api/v1/auth/login",
        content=(chunk for chunk in [b'{"email":"', b"x" * 70000, b'"}']),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413, response.text
    assert response.json()["code"] == "BODY_TOO_LARGE"


def test_spoofed_multipart_fields_and_checksum_integrity(world, client):
    prefix = f"/api/v1/projects/{world[2]['id']}"
    response = client.post(
        prefix + "/sources",
        files={"file": synthetic_files()["txt"]},
        data={"metadata": '{"name":"Synthetic"}', "project_id": world[3]["id"]},
    )
    assert response.status_code == 422
    data = upload(client, world[2]).json()
    from app.core.config import get_settings
    from app.storage.local import LocalStorage

    storage = LocalStorage(get_settings().storage_root)
    key = f"{world[2]['id']}/{data['source']['id']}/{data['version']['id']}.bin"
    storage.path(uuid.UUID(world[2]["id"]), key).write_bytes(b"tampered")
    response = client.get(
        prefix + f"/sources/{data['source']['id']}/versions/{data['version']['id']}/download"
    )
    assert response.status_code == 503 and response.json()["code"] == "STORAGE_INTEGRITY_ERROR"


def test_phase1_upgrade_preserves_existing_foundation(world, client):
    # Autouse cleanup leaves the new ingestion tables empty; retain populated foundation rows.
    expected = world[2]
    configuration = Config("alembic.ini")
    try:
        command.downgrade(configuration, "0002_project_codes")
        command.upgrade(configuration, "head")
        grant_runtime()
        result = client.get(f"/api/v1/projects/{expected['id']}")
        assert result.status_code == 200
        assert result.json()["project_code"] == expected["project_code"]
        assert result.json()["my_role"] == "PROJECT_ADMIN"
        assert len(client.get(f"/api/v1/projects/{expected['id']}/audit").json()["items"]) == 2
        assert upload(client, expected).status_code == 201
    finally:
        command.upgrade(configuration, "head")
        grant_runtime()
