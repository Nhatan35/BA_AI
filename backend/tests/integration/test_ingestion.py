import hashlib
import io
import json
import uuid
from dataclasses import replace

import pytest
from pypdf import PdfWriter
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_engine, set_actor
from app.modules.evidence.models import Evidence
from app.modules.sources.models import ParsedSection, SourceVersion
from app.modules.sources.parsers import Limits, ParseFailure, StructuredParser
from app.storage.local import LocalStorage, storage_key
from tests.conftest import sign_in
from tests.fixtures import DEMO, synthetic_files


def upload(client, project, file=None, metadata=None, source=None):
    file = file or synthetic_files()["txt"]
    path = f"/api/v1/projects/{project['id']}/sources" + (f"/{source}/versions" if source else "")
    return client.post(
        path,
        files={"file": file},
        data={"metadata": json.dumps(metadata or {"name": "Demo Clinic Booking", "source_type": "TEXT"})}
        if not source
        else {},
    )


def evidence(client, project, result, line=1):
    return client.post(
        f"/api/v1/projects/{project['id']}/evidence",
        json={
            "source_id": result["source"]["id"],
            "source_version_id": result["version"]["id"],
            "locator": {"kind": "LINE", "start": line},
            "classification": "QUESTION" if line == 2 else "FACT",
        },
    )


@pytest.mark.parametrize("kind", ["txt", "md", "pdf", "docx", "csv", "xlsx"])
def test_six_format_upload_parse_download(kind, world, client):
    project = world[2]
    fixture = synthetic_files()[kind]
    response = upload(client, project, fixture)
    assert response.status_code == 201, response.text
    source, version = response.json()["source"], response.json()["version"]
    assert version["parser_status"] == "PARSED", response.text
    assert "storage_key" not in response.text
    base = f"/api/v1/projects/{project['id']}/sources/{source['id']}/versions/{version['id']}"
    parsed = client.get(base + "/parsed").json()
    assert parsed["items"] and all(row["project_id"] == project["id"] for row in parsed["items"])
    assert client.get(base + "/download").content == fixture[1]
    assert version["checksum"] == hashlib.sha256(fixture[1]).hexdigest()
    if kind == "docx":
        assert [i["locator"]["kind"] for i in parsed["items"]] == [
            "DOCX_PARAGRAPH",
            "DOCX_PARAGRAPH",
            "DOCX_TABLE",
            "DOCX_PARAGRAPH",
        ]
    if kind == "xlsx":
        assert parsed["items"][2]["cells"]["B"] == "=1+1"
    section = parsed["items"][0]
    result = client.post(
        f"/api/v1/projects/{project['id']}/evidence",
        json={
            "source_id": source["id"],
            "source_version_id": version["id"],
            "locator": section["locator"],
            "classification": "FACT",
        },
    )
    assert result.status_code == 201, result.text
    assert result.json()["exact_reference"] == section["display_reference"]


def test_demo_history_search_confirmation_audit(world, client):
    project = world[2]
    uploaded = upload(client, project).json()
    records = [evidence(client, project, uploaded, line).json() for line in (1, 2, 3)]
    assert records[1]["classification"] == "QUESTION"
    assert "not yet been decided" in records[1]["extracted_text"]
    assert all(row["confirmed_by"] is None for row in records)
    prefix = f"/api/v1/projects/{project['id']}"
    results = client.get(prefix + "/search", params={"q": "cancellation"}).json()
    assert len(results["items"]) == 3
    assert all(row["source_version_id"] == uploaded["version"]["id"] for row in results["items"])
    confirmed = client.post(
        prefix + f"/evidence/{records[0]['id']}/confirmation",
        json={"confirmed": True, "expected_revision": 1},
    )
    assert confirmed.status_code == 200 and confirmed.json()["confirmed_by"] == str(world[0].id)
    changed = client.patch(
        prefix + f"/evidence/{records[0]['id']}",
        json={"summary": "A source statement, not an approved requirement", "expected_revision": 2},
    )
    assert changed.status_code == 200 and changed.json()["confirmed_by"] is None
    source_id = uploaded["source"]["id"]
    second = upload(
        client, project, ("second.txt", b"Another synthetic statement", "text/plain"), source=source_id
    ).json()
    assert second["version"]["version_number"] == 2
    firstbase = prefix + f"/sources/{source_id}/versions/{uploaded['version']['id']}"
    assert client.get(firstbase + "/download").content == DEMO.encode()
    assert client.post(firstbase + "/reparse").status_code == 201
    assert len(client.get(firstbase + "/parses").json()["items"]) == 2
    assert (
        client.get(prefix + f"/evidence/{records[0]['id']}").json()["parse_run_id"]
        == uploaded["version"]["parse_run_id"]
    )
    assert len(client.get(prefix + "/search?q=cancellation").json()["items"]) == 3
    archived = client.patch(
        prefix + f"/sources/{source_id}", json={"status": "ARCHIVED", "expected_revision": 1}
    )
    assert archived.status_code == 200
    assert client.get(prefix + "/search?q=cancellation").json()["items"] == []
    assert len(client.get(prefix + "/search?q=cancellation&include_inactive=true").json()["items"]) == 3
    assert client.get(firstbase + "/download").content == DEMO.encode()
    assert upload(client, project, source=source_id).status_code == 409
    logs = client.get(prefix + "/audit?limit=100").json()["items"]
    assert {
        "SOURCE_CREATED",
        "SOURCE_VERSION_UPLOADED",
        "PARSE_REQUESTED",
        "PARSE_STARTED",
        "PARSE_COMPLETED",
        "EVIDENCE_CREATED",
        "EVIDENCE_CONFIRMED",
        "EVIDENCE_UPDATED",
        "SOURCE_ARCHIVED",
        "SOURCE_DOWNLOADED",
    }.issubset({row["action"] for row in logs})
    assert DEMO not in json.dumps(logs)


def test_cross_project_all_paths_and_forged_links(world, client):
    a_user, b_user, a, b = world
    sign_in(client, b_user.email)
    private = upload(client, b, ("private-b-secret.txt", b"Private zebra cancellation", "text/plain")).json()
    ev = evidence(client, b, private).json()
    sign_in(client, a_user.email)
    ap = f"/api/v1/projects/{a['id']}"
    bp = f"/api/v1/projects/{b['id']}"
    tail = f"/sources/{private['source']['id']}/versions/{private['version']['id']}"
    for prefix in (ap, bp):
        for route in (
            f"/sources/{private['source']['id']}",
            tail,
            tail + "/parsed",
            tail + "/download",
            tail + "/parses",
            f"/evidence/{ev['id']}",
        ):
            result = client.get(prefix + route)
            assert result.status_code == 404, (route, result.text)
            assert "private-b" not in result.text and "zebra" not in result.text
        assert (
            client.patch(
                prefix + f"/sources/{private['source']['id']}",
                json={"name": "Attack", "expected_revision": 1},
            ).status_code
            == 404
        )
        assert (
            client.patch(
                prefix + f"/evidence/{ev['id']}", json={"summary": "Attack", "expected_revision": 1}
            ).status_code
            == 404
        )
        assert client.post(prefix + tail + "/reparse").status_code == 404
        assert (
            client.post(
                prefix + f"/evidence/{ev['id']}/confirmation",
                json={"confirmed": True, "expected_revision": 1},
            ).status_code
            == 404
        )
    assert client.get(bp + "/sources").status_code == 404
    assert client.get(bp + "/evidence").status_code == 404
    assert client.get(bp + "/search?q=cancellation").status_code == 404
    assert upload(client, b).status_code == 404
    assert upload(client, a, source=private["source"]["id"]).status_code == 404
    assert evidence(client, a, private).status_code == 404
    assert upload(client, a, metadata={"name": "Spoof", "project_id": b["id"]}).status_code == 422
    own = upload(client, a).json()
    assert (
        client.patch(
            ap + f"/sources/{own['source']['id']}",
            json={"supersedes_source_id": private["source"]["id"], "expected_revision": 1},
        ).status_code
        == 404
    )
    for path in ("/sources", "/evidence", "/search?q=cancellation"):
        result = client.get(ap + path)
        assert "private-b" not in result.text and private["source"]["id"] not in result.text
    # Even an actor with access to BOTH projects may not resolve B objects through A.
    sign_in(client, b_user.email)
    assert client.post(bp + "/members", json={"email": a_user.email, "role": "BA"}).status_code == 201
    sign_in(client, a_user.email)
    assert client.get(ap + tail + "/download").status_code == 404
    assert client.get(ap + "/search?q=zebra").json()["items"] == []


@pytest.mark.parametrize(
    "file,status",
    [
        (("../escape.txt", b"hi", "text/plain"), 422),
        (("exe.txt", b"MZ\x00binary", "text/plain"), 415),
        (("bad.exe", b"MZ", "application/octet-stream"), 415),
        (("bad.txt", b"", "text/plain"), 422),
        (("fake.pdf", b"plain text", "application/pdf"), 415),
        (("fake.txt", b"text", "application/pdf"), 415),
    ],
)
def test_rejected_uploads_leave_no_source(world, client, file, status):
    assert upload(client, world[2], file).status_code == status
    assert client.get(f"/api/v1/projects/{world[2]['id']}/sources").json()["items"] == []


def test_corrupt_and_ocr_required_keep_original(world, client):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    buffer = io.BytesIO()
    writer.write(buffer)
    for file, expected in [
        (("corrupt.pdf", b"%PDF-1.7\ncorrupt", "application/pdf"), "FAILED"),
        (("scan.pdf", buffer.getvalue(), "application/pdf"), "UNSUPPORTED_OR_OCR_REQUIRED"),
    ]:
        result = upload(client, world[2], file)
        assert result.status_code == 201
        data = result.json()
        assert data["version"]["parser_status"] == expected
        assert "Traceback" not in result.text and "storage" not in result.text
        path = (
            f"/api/v1/projects/{world[2]['id']}/sources/{data['source']['id']}"
            f"/versions/{data['version']['id']}/download"
        )
        assert client.get(path).content == file[1]


def test_duplicate_awareness_is_project_scoped(world, client):
    a_user, b_user, a, b = world
    first = upload(client, a).json()
    second = upload(client, a).json()
    assert second["version"]["duplicate_version_ids"] == [first["version"]["id"]]
    sign_in(client, b_user.email)
    foreign = upload(client, b).json()
    assert foreign["version"]["duplicate_version_ids"] == []
    sign_in(client, a_user.email)


def test_immutable_versions_sections_parse_and_cross_scope_fk(world, client, owner_engine):
    first = upload(client, world[2]).json()
    ev = evidence(client, world[2], first).json()
    for query in (
        "UPDATE source_versions SET original_filename='tamper.txt'",
        "DELETE FROM source_versions",
        "UPDATE parsed_sections SET text='tamper'",
        "DELETE FROM parsed_sections",
        "UPDATE parse_runs SET parser_status='FAILED'",
        "UPDATE evidence SET source_version_id=gen_random_uuid()",
    ):
        with pytest.raises(DBAPIError), owner_engine.begin() as connection:
            connection.execute(text(query))
    for query in ("UPDATE source_versions SET checksum='tamper'", "DELETE FROM parsed_sections"):
        with Session(get_engine()) as db:
            set_actor(db, world[0].id)
            with pytest.raises(DBAPIError):
                db.execute(text(query))
    sign_in(client, world[1].email)
    second = upload(client, world[3]).json()
    with pytest.raises(DBAPIError), owner_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO source_versions (id,project_id,source_id,version_number,original_filename,"
                "storage_key,mime_type,file_size,checksum,created_by,created_at) "
                "SELECT gen_random_uuid(), :project, source_id, 9,'x.txt','forged','text/plain',1,"
                "checksum,created_by,created_at FROM source_versions WHERE id=:version"
            ),
            {"project": world[2]["id"], "version": second["version"]["id"]},
        )
    with Session(get_engine()) as db:
        set_actor(db, world[0].id)
        assert (
            db.scalar(select(SourceVersion).where(SourceVersion.id == uuid.UUID(second["version"]["id"])))
            is None
        )
        assert db.scalar(select(Evidence).where(Evidence.id == uuid.UUID(ev["id"]))) is not None
    with Session(get_engine()) as db:
        assert db.scalars(select(ParsedSection)).all() == []


def test_bad_locator_quote_and_spoofed_confirmation(world, client):
    data = upload(client, world[2]).json()
    base = {
        "source_id": data["source"]["id"],
        "source_version_id": data["version"]["id"],
        "classification": "FACT",
        "locator": {"kind": "LINE", "start": 99},
    }
    prefix = f"/api/v1/projects/{world[2]['id']}/evidence"
    assert client.post(prefix, json=base).status_code == 422
    base["locator"]["start"] = 1
    base["extracted_text"] = "Cancellation must occur 24 hours ahead"
    assert client.post(prefix, json=base).status_code == 422
    del base["extracted_text"]
    base["confirmed_by"] = str(world[0].id)
    assert client.post(prefix, json=base).status_code == 422


def test_configured_limits_and_storage_guards(world, client, tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "upload_max_bytes", 20)
    assert upload(client, world[2]).status_code == 413
    storage = LocalStorage(tmp_path)
    project, source, version = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    key = storage_key(project, source, version)
    storage.put(project, key, b"raw")
    with pytest.raises(FileExistsError):
        storage.put(project, key, b"overwrite")
    assert storage.read(project, key) == b"raw"
    for invalid in ("../escape", key.replace(str(project), str(uuid.uuid4())), "C:/escape.txt"):
        with pytest.raises(ValueError):
            storage.read(project, invalid)


@pytest.mark.parametrize(
    "kind,changed",
    [
        ("csv", {"csv_max_rows": 1}),
        ("xlsx", {"spreadsheet_max_rows": 1}),
        ("pdf", {"parse_max_pages": 0}),
        ("txt", {"parse_max_characters": 5}),
        ("docx", {"parse_max_expanded_bytes": 10}),
    ],
)
def test_parser_limits(kind, changed):
    limits = replace(Limits.configured(), **changed)
    with pytest.raises(ParseFailure):
        StructuredParser("." + kind).parse(synthetic_files()[kind][1], limits)
