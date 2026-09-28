# Windows local development — Phases 1 and 2

## Phase 2 upgrade and workflow

Phase 1 is accepted. Run locked dependency sync, then Alembic upgrade and explicit runtime grants as in the setup below; head is `0004_ingestion_guards`. New libraries are python-multipart0.0.32, pypdf6.19.0, python-docx1.2.0, openpyxl3.1.5 and defusedxml0.7.1, pinned in uv.lock. Startup now checks RLS/non-owner privileges on all eight project tables. Phase 2 behavior/technical limits: [INGESTION_AND_STORAGE](INGESTION_AND_STORAGE.md); executed evidence: [PHASE_2_RESULT](PHASE_2_RESULT.md).

In a project, open Sources → upload a synthetic TXT/MD/text PDF/DOCX/CSV/XLSX with metadata → inspect status, versions and ordered parsed passages → download original → choose a passage/Create evidence → select class and save → inspect Evidence → search the project. BA/PROJECT_ADMIN can upload/edit/cite; other roles read, with BUSINESS_OWNER/PROJECT_ADMIN permitted to confirm evidence only. A no-text PDF explicitly reports OCR-required status. Upload a replacement through the source detail to preserve old bytes/citations; reparse appends an attempt. Archive/supersede explicitly in source metadata.

Default raw storage is workspace var/storage; optional STORAGE_ROOT overrides it and must be private/outside public web files. All parser/upload environment settings and defaults are in backend/.env.example and the ingestion document. Changes require restart. Test storage uses separate var/test-storage and browser servers var/e2e-storage. Run backend tests before browser seed/servers because backend tests truncate the shared dedicated test DB.

Read-only operator reconciliation, from backend:

```powershell
$env:PYTHONPATH = '.'
& '.\.venv\Scripts\python.exe' scripts/inspect_storage.py
```

This prints counts only and never deletes files. Raw storage and PostgreSQL both need backup; retention and automatic recovery are not implemented. Existing Start/Stop-Phase1TestServers script names remain for compatibility and now run the complete Phase 2 app; no PostgreSQL system service or system configuration changes are needed.

Run commands in PowerShell from the workspace root unless a `Set-Location` command says otherwise. Use synthetic information. No real patient data or LLM credential is required. All paths below are relative to the workspace, so it can be moved.

## Environment diagnosis and resolution

The system `python`/`python3` commands resolve to Windows Store execution aliases and cannot launch an interpreter. No `py`, Docker, PostgreSQL service/client, uv or pnpm was found on PATH. Node 24.21.0, npm 11.19.0 and Git 2.55.0 work. No application architecture was replaced.

Installed and exercised workspace-local uv 0.12.19, CPython 3.13.15 and PostgreSQL 17.11. Python is under `.tools/python/`, the backend virtual environment under `backend/.venv/`, PostgreSQL server/client binaries under `.tools/postgresql/pgsql/`. No system PATH, registry, Windows service or system Python installation was changed. Tool archives and local credentials/data are ignored by version control. Network installation and some subprocess writes required the environment's approved sandbox escalation; this is an execution-environment restriction, not an application requirement.

The official PostgreSQL archive contains pgAdmin paths exceeding this Windows environment's path limit. The installer script extracts only `bin`, `lib`, `share` and server/client licenses. The archive passed ZIP integrity inspection and is pinned to the observed SHA-256. Download sources: [uv installation](https://docs.astral.sh/uv/getting-started/installation/) and [EDB Windows binaries](https://www.enterprisedb.com/download-postgresql-binaries). The uv archive hash was also checked against GitHub release metadata. The PostgreSQL hash pins the downloaded artifact; it is not a claim of an independently verified vendor signature.

## First setup with portable PostgreSQL

```powershell
# Downloads verified pinned archives; allow network access if your environment requires it.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/Install-LocalTools.ps1
$env:UV_PYTHON_INSTALL_DIR = Join-Path (Get-Location) '.tools/python'
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.tools/cache'
& '.\.tools\uv\uv.exe' sync --project backend --locked

# Creates private loopback-only cluster, SCRAM credentials, and starts it on port 55432.
powershell -NoProfile -File scripts/Start-LocalPostgres.ps1

Set-Location backend
$env:PYTHONPATH = '.'
& '.\.venv\Scripts\python.exe' scripts/setup_database.py
& '.\.venv\Scripts\python.exe' -m alembic upgrade head
& '.\.venv\Scripts\python.exe' scripts/grant_runtime.py

# Password is prompted twice and is not passed in shell history or shipped with the app.
& '.\.venv\Scripts\python.exe' -m app.cli bootstrap-admin --email 'admin@example.com' --display-name 'Project operator'
& '.\.venv\Scripts\python.exe' -m app.cli create-user --email 'ba@example.com' --display-name 'BA'
```

Choose your own passwords (12–1024 characters); the example emails are synthetic identities, not default accounts. Bootstrap works only when the user registry is empty and is serialized with a PostgreSQL advisory lock. Later provisioning requires an existing active system-admin account and access to migration/operator credentials. The CLI is an operator boundary, not a public registration endpoint. System-admin status grants no private-project access or clinical/business approval.

`setup_database.py` creates named local roles `medical_owner` and `medical_app`, plus `medical_ba` and the dedicated disposable `medical_ba_test` database. It generates private passwords into ignored `backend/.env`; it preserves an existing `.env`. If named roles already exist but configuration is absent, it stops rather than resetting credentials; configure the examples manually with the database operator. Keep migration/operator credentials out of the running application environment in deployment.

Restart PostgreSQL later with the same start script. Stop it from the workspace root with:

```powershell
powershell -NoProfile -File scripts/Stop-LocalPostgres.ps1
```

Do not run portable PostgreSQL and Docker Compose on port 55432 simultaneously.

## Start backend and frontend

Backend terminal, from `backend/`:

```powershell
& '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend terminal, from the workspace root:

```powershell
Set-Location frontend
$env:NEXT_TELEMETRY_DISABLED = '1'
$env:npm_config_cache = Join-Path (Split-Path -Parent (Get-Location).Path) '.npm-cache'
npm.cmd ci
$env:BACKEND_URL = 'http://127.0.0.1:8000'
npm.cmd run dev
```

Open `http://127.0.0.1:3000/login`. Sign in with the provisioned account; create a project; open its workspace; use settings to add the other existing account by email and assign a project role. The creator receives PROJECT_ADMIN, with no automatic BUSINESS_OWNER or MEDICAL_SME role. Another project administrator must change your own membership. Project codes are generated as `PRJ-001`, etc.; UUIDs remain stable API identifiers.

API health: `http://127.0.0.1:8000/api/v1/health`; OpenAPI UI: `http://127.0.0.1:8000/docs`. Documentation/schema contains no project records or credentials. Mutating API clients must send an explicitly allowed `Origin`, authenticate with the session cookie, and send `X-CSRF-Token` from login or `/auth/me`. The frontend does this automatically using same-origin API rewrites. Runtime authorization is required even when a UI hides controls.

For a local production frontend build, set BACKEND_URL before `npm.cmd run build`, then `npm.cmd run start`. Next.js compiles rewrite destinations into the build; rebuild if that destination changes. Cookie Secure must be true and allowed origins must use HTTPS before enabling backend production configuration.

## Configuration and session behavior

Examples: [backend configuration](../backend/.env.example), [frontend configuration](../frontend/.env.example).

| Setting | Development meaning |
|---|---|
| DATABASE_URL | Dedicated non-owner PostgreSQL runtime role; backend refuses owner/superuser/BYPASSRLS role at startup |
| MIGRATION_DATABASE_URL | Owner/operator connection for Alembic/CLI/grants; never used by API services |
| TEST_DATABASE_URL / TEST_MIGRATION_DATABASE_URL | Runtime/owner pair for a dedicated database ending `_test`; tests refuse other targets |
| ALLOWED_ORIGINS | Explicit JSON list, default localhost/127.0.0.1 port 3000; no wildcard/CORS credential access |
| SESSION_HOURS | Absolute session lifetime, default 8 hours, configurable; no silent renewal |
| COOKIE_SECURE | false only for loopback HTTP development; production config requires true |
| LOGIN_MAX_ATTEMPTS / LOGIN_WINDOW_SECONDS | Defaults 10 per IP/account per 300 seconds; bounded single-process limiter |

Authentication uses Argon2id password hashes and random 256-bit opaque cookies. Only the SHA-256 cookie digest is persisted. Cookies are HttpOnly and SameSite=Strict. CSRF is derived from the cookie secret and returned through authenticated responses; the frontend holds it only for requests. Login validates origin; every authenticated mutation validates origin plus CSRF. Login rotates/revokes the previous cookie, logout revokes the DB session and clears the cookie, expired/inactive users are rejected. Membership status/role is checked afresh on project requests; no project permission is cached in a token. Passwords, cookies and document text are excluded from audit metadata/errors.

These lifetimes/limits and English UI are **ASSUMPTION — NEEDS CONFIRMATION** technical development defaults, not healthcare business policies. Production scale needs a shared rate limiter, trusted reverse-proxy/client-IP configuration, TLS and deployment review. There is no password reset/self-signup/SSO implementation in Phase 1.

## PostgreSQL migrations and permissions

```powershell
# From backend/
$env:PYTHONPATH = '.'
& '.\.venv\Scripts\python.exe' -m alembic current
& '.\.venv\Scripts\python.exe' -m alembic upgrade head
& '.\.venv\Scripts\python.exe' scripts/grant_runtime.py
& '.\.venv\Scripts\python.exe' -m alembic check
```

Migrations own the schema. Grants are explicit and reapplied after upgrades; the runtime role cannot create/drop tables, mutate audit, change users, delete project history or bypass RLS. The narrowly scoped SECURITY DEFINER membership predicates avoid recursive RLS; their search paths are pinned, and function execution is granted explicitly. The backend sets an authenticated actor transaction-locally; this context resets when pooled connections are returned. Database credentials are trusted server/operator secrets; the row policies do not protect against theft of those credentials and arbitrary session impersonation.

`alembic downgrade base` is supported for disposable test/development databases but removes all Phase 1 data. Do not use it against valued data. The test suite executes fresh upgrade, downgrade to base, and re-upgrade on the dedicated test database. No manual schema definition is maintained alongside migrations.

## Tests and build

```powershell
# From backend/
$env:PYTHONPATH = '.'
& '.\.venv\Scripts\ruff.exe' check app migrations scripts tests --no-cache
& '.\.venv\Scripts\python.exe' -m pytest -q

# From frontend/
npm.cmd run typecheck
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run build
```

Backend tests use actual PostgreSQL and the non-owner runtime role. They erase only the explicitly configured `_test` database's synthetic rows. Never point test settings at production. They do not switch to SQLite or silently skip required isolation checks.

Browser tests, from the workspace root after backend tests finish:

```powershell
Set-Location backend
$env:PYTHONPATH = '.'
& '.\.venv\Scripts\python.exe' scripts/seed_e2e.py
Set-Location ..
powershell -NoProfile -File scripts/Start-Phase1TestServers.ps1
Set-Location frontend
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Split-Path -Parent (Get-Location).Path) '.tools/browsers'
npx.cmd playwright install chromium
npm.cmd run test:e2e
Set-Location ..
powershell -NoProfile -File scripts/Stop-Phase1TestServers.ps1
```

Browser fixtures have random synthetic credentials in ignored `var/e2e-fixtures.json`, never source-controlled defaults. Test servers use port 8001 and port 3000 with the `_test` database and a higher synthetic-test login limit. Stop an ordinary frontend using port 3000 before starting them. Do not run backend reset tests while browser tests are using that database. Hidden test-server processes and descendants are stopped only after verifying their recorded commands. PostgreSQL remains available for normal development.

## Docker alternative (configured, not exercised here)

If Docker Desktop is installed and running, create the private secret file first (the portable start script does this if already used). Otherwise from the root:

```powershell
New-Item -ItemType Directory -Path var -Force | Out-Null
$secretBytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try { $rng.GetBytes($secretBytes) } finally { $rng.Dispose() }
[System.IO.File]::WriteAllText((Join-Path (Get-Location) 'var/postgres-password.txt'), [Convert]::ToBase64String($secretBytes))
docker compose -f infra/compose.yaml up -d
Set-Location backend
$env:PYTHONPATH = '.'
& '.\.venv\Scripts\python.exe' scripts/setup_database.py
& '.\.venv\Scripts\python.exe' -m alembic upgrade head
& '.\.venv\Scripts\python.exe' scripts/grant_runtime.py
```

Generate a secret only for a new development cluster; do not overwrite an existing cluster's password file. Compose binds PostgreSQL to loopback, keeps data in a named volume and supplies the generated password through a file secret. Docker is absent in this environment, so Compose startup is **NOT RUN**. The tested path is native workspace PostgreSQL. For a pre-existing local PostgreSQL installation, configure the same owner/runtime separation in `.env`, or use the setup script only on a dedicated development instance with the appropriate host/port/password file.
