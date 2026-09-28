# Phase 1 result — foundation

Phase 1 implementation complete for review. No Phase 2 feature implementation. The original 53 baseline files remain immutable references. The user's DEC-MVP-001–007 are recorded in [baseline assessment](BASELINE_ASSESSMENT.md) and reflected in the architecture/schema/API plans.

## Environment

Initial blocker: Python aliases fail; no launcher, Docker or PostgreSQL installation/service found. Resolved through workspace-local uv 0.12.19, Python 3.13.15 and native PostgreSQL 17.11. Node 24.21.0/npm 11.19.0/Git 2.55.0 are available. The workspace still has no Git repository metadata. Windows archive path limits were resolved by omitting pgAdmin/StackBuilder and extracting server/client files only. PostgreSQL is loopback-only on port 55432 with SCRAM credentials; runtime and owner roles are separate. No system software replacement, PATH modification or Windows service installation was used.

Full commands: [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md). Runtime dependencies are locked in `backend/uv.lock` and `frontend/package-lock.json`. Docker Compose configuration exists; native PostgreSQL is the exercised development path.

## Implemented scope

- Local normalized email/password users, ACTIVE/INACTIVE behavior, Argon2id password hashing and safe response schemas.
- Revocable random-cookie sessions with absolute expiry, token digests in PostgreSQL, origin/CSRF protection, login rotation/logout and bounded login rate control.
- Safe prompted-password operator CLI for first admin, additional users and deactivation. No hard-coded or automatically shipped login.
- Stable Project UUIDs plus PRJ display codes, editable scope/context/status with optimistic revision checks.
- ProjectMember connects User/Project/canonical role/status; active membership required for every private project route. Roles differ per project.
- PROJECT_ADMIN member administration and project audit access; other roles read project/member context. Global system admin has no membership bypass. Self-membership changes are rejected.
- PostgreSQL row policies, immutable project/member identities, separate runtime grants, append-oriented project audit/platform security events and atomic domain/audit commits.
- Next.js login, projects/create, workspace and settings/members UI; safe unauthorized handling and admin audit display.

Only User, AuthSession, Project, ProjectMember, AuditLog and SecurityEvent are implemented. Source ingestion, Evidence, AI/RAG, requirements/reviews, graph, changes/impact, artifacts and evaluation remain future modules. No clinical or business approval capability is implemented or granted by the AI.

## Database/migrations

| Revision | Change |
|---|---|
| 0001_foundation | Six tables, FK/unique/check constraints/indexes, project/member/audit RLS policies, pinned authorization predicates, immutable identity and append-only audit triggers |
| 0002_project_codes | Independent PRJ display-code sequence; preserves existing project identifiers and safe sequence initialization |

Alembic owns schema creation/upgrades/downgrades. Operator setup creates two named development databases and generates private credentials in ignored `.env`. Explicit grants exclude ownership/BYPASSRLS/superuser, user mutation, project deletion and audit mutation. Backend startup rejects unsafe database roles and absent/disabled project RLS. Fresh upgrade, upgrade from 0001, downgrade to base/re-upgrade and ORM/migration consistency checks have been executed on PostgreSQL.

## API and UI

Implemented under `/api/v1`: GET health; POST auth/login/logout; GET auth/me; GET/POST projects; GET/PATCH projects/{id}; GET/POST projects/{id}/members; GET/PATCH projects/{id}/members/{member_id}; GET projects/{id}/audit. Schemas and permissions: [API_PLAN.md](API_PLAN.md).

UI routes: `/login`, `/projects`, `/projects/[projectId]`, `/projects/[projectId]/settings`, with `/` redirecting to projects. The settings screen adds existing provisioned users by email, changes other members' roles, activates/deactivates membership and displays safe audit events. The same-origin proxy retains backend authorization and CSRF requirements.

## Authorization/security evidence

An authenticated User A belonging to Project A cannot read Project B, its member list/member IDs or audit, including direct guessed-ID calls. Inaccessible and absent records both return generic 404. A member without PROJECT_ADMIN gets 403 for administration in an accessible project. Non-owner PostgreSQL reads without actor context return no project rows; context is reset on connection reuse. Foreign membership writes are rejected by RLS. Inactive membership/user and revoked/expired sessions deny access. Runtime project permissions are not stored in the cookie.

Responses never serialize password_hash. Validation failures do not echo submitted passwords/raw fields. Audit metadata contains roles/statuses/revision references rather than passwords/tokens/project text. Project mutation + audit roll back together on failure. Database triggers and grants reject audit updates/deletion and project/member reassignment. Startup rejects owner/bypass connections and disabled RLS. SQL values use parameters, not raw user-string SQL interpolation.

## Executed verification

| Command/check | Result |
|---|---|
| `python -m pytest -q` against PostgreSQL/runtime role | **31 passed, 1 dependency deprecation warning, 19.85s** |
| `ruff check app migrations scripts tests --no-cache` | PASS after import formatting correction |
| `python -m alembic check` | PASS: No new upgrade operations detected |
| `npm.cmd run typecheck` | PASS |
| `npm.cmd run build` | PASS, exit 0; all Phase 1 routes compiled in final production build |
| Chromium `npm.cmd run test:e2e` | 3 passed in 13.8s: login/redirect, project/member roles/revocation, guessed-ID isolation |
| Live test backend `/api/v1/health` | 200, `{status: ok}` against native PostgreSQL |
| Frontend `/login` | 200; actual pages exercised by Chromium |
| Baseline SHA-256/document/script checks | PASS: all 53 originals unchanged, all 23 sheets match, 46 local links resolve, all PowerShell scripts parse |

The initial browser run exposed an ambiguous selector caused by Next.js's route announcer and an assertion made before navigation settled. Tests were corrected to target the application error and await the workspace URL; the corrected full suite passed. No test success was inferred from code inspection. Backend tests are synthetic and refuse any database name not ending `_test`.

Final verification completed on 2026-09-28. Backend lint, PostgreSQL tests, Alembic consistency, TypeScript and production build all exited 0; Chromium suite passed. The final backend run also covers unsafe owner connections, disabled RLS, and consistent safe 401/404/413 errors. Browser test processes were stopped after verification; native PostgreSQL remains available for development. No external execution blocker remains for the tested native path.

## Not run / deliberate limits

- Docker Compose startup: **NOT RUN**, Docker is absent; native PostgreSQL path passed.
- Enterprise SSO/social login, patient-data testing, source ingestion/AI/model evaluations, requirement approval and other later features: outside Phase 1, not represented as completed tests.
- Production TLS/deployment, shared rate limiting, restore/retention policies and production security/privacy release review: not a Phase 1 local-development release claim.

There is one dependency deprecation warning for Starlette TestClient's current httpx integration; tests pass and the lockfile preserves the verified combination. No known broken application state is left. Production rate limiting needs shared enforcement across workers and trusted client-IP configuration; the current bounded limiter is single-process. MFA/password reset/public signup are absent. Full project context history/stakeholder/policy revisions, multi-role membership and generic idempotency keys remain later work; current writes have revision/uniqueness/transaction protection and safe audit events.

## Decisions, assumptions and entry conditions

Locked: local identity; no AI approval; active-membership project isolation; member-scoped source access in later phases; provider abstraction/synthetic data; CR after BASELINED; clinical review default false with mandatory SME gate on impact.

**ASSUMPTION — NEEDS CONFIRMATION:** active users may create projects and receive PROJECT_ADMIN; one role per membership; other administrators manage one's own membership; operator-only provisioning; eight-hour sessions and 10-attempt/300-second login control; English UI. These reversible defaults are explicit in the decision register. Project administration never substitutes for Business Owner or Medical SME approval authority.

Phase 2 entry: review Phase 1, retain/test the project authorization context and RLS for every new domain table/query/file/job, settle ingestion resource bounds/storage access, add format fixtures and version-specific citation tests, and confirm source access remains membership-based. No provider/patient data is required to begin source registry work. Do not auto-advance after this handoff.

## Files added/changed

Root README/ignore rules; backend application/config, routers/services/repositories/models/CLI; two Alembic migrations and config; PostgreSQL setup/grants and synthetic browser seed; backend tests and uv lock; frontend package/lock/config, typed API, shell/pages/CSS and Playwright tests; native-tool/start/stop/test-server scripts; Compose and boundary READMEs; architecture/data/API/implementation/baseline understanding updates; this result and Windows guide. Exact tracked-intent paths are in [phase-1-files.txt](phase-1-files.txt). Local tools, database data, private `.env`, random fixture credentials, caches and reports are excluded. Original numbered starter-kit files were not modified.
