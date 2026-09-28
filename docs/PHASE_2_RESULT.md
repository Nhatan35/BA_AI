# Phase 2 result — ingestion, evidence and scoped search

Implemented on 2026-09-28, extending accepted Phases 0/1. Phase 2 only; Phase 3 is not started. DEC-P2-001–006 are retained. Synthetic information only, no patient records or live provider calls.

## 1. Implemented

Source registry/upload/metadata/lifecycle, immutable raw SourceVersions, separate parse attempts/ordered sections, safe original downloads, manual exact-reference Evidence with seven classes and human confirmation, lexical project search, UI, transactional audit and adversarial regression tests. Original kit files remain preserved.

## 2. Migrations

`0003_ingestion` adds sources/source_versions/parse_runs/parsed_sections/evidence, composite lineage FKs, checks/indexes, GIN full-text index, project RLS/editor/confirmer policies and history triggers. `0004_ingestion_guards` adds key/ordinal/attempt checks and append/confirmation guards. Main DB upgraded from accepted0002 without changing Phase1 schema; explicit runtime grants applied. Dedicated test DB exercised fresh downgrade/base→head and populated0002→head preservation. Alembic check: no new upgrade operations detected.

## 3. Supported formats

TXT, MD, text PDF, DOCX, CSV, XLSX. Locked python-multipart0.0.32, pypdf6.19.0, python-docx1.2.0, openpyxl3.1.5, defusedxml0.7.1. UTF-8 text/CSV; JSON and OCR intentionally absent.

## 4. Storage

Local private Storage adapter, generated project/source/version UUID keys, exclusive raw writes, path containment, immutable DB raw metadata, SHA-256/size integrity checks, authorized attachment download. Project-local duplicate awareness preserves uploads. API exposes no storage paths. Separate test storage roots; read-only reconciliation verified on main DB: registered0/on-disk0/missing0/unreferenced0/unfinished0.

## 5. Parser behavior

Lines, PDF pages, DOCX paragraphs/headings/tables in body order, CSV logical rows/header/cells, XLSX sheet/row/cell references. Formulas/links/macros never executed. Separate PENDING/PROCESSING/terminal history, safe FAILED/UNSUPPORTED errors, no-text PDF UNSUPPORTED_OR_OCR_REQUIRED. Explicit reparse preserves previous extraction/citations. Configurable size/row/sheet/character/page/time/concurrency/expansion controls: [INGESTION_AND_STORAGE](INGESTION_AND_STORAGE.md).

## 6. Source/Evidence API

Implemented project-scoped sources POST/GET/detail/PATCH, versions POST/list/detail, download/parsed/parses/reparse, evidence POST/list/detail/PATCH/confirmation and search GET. Strict field/locator/quote validation; pagination/revisions; immutable provenance. Membership, Origin/CSRF and generic inaccessible404 reuse Phase1. Exact routes/bodies/errors are in [API_PLAN](API_PLAN.md) and the ingestion contract.

## 7. Frontend

Workspace links plus Sources register/upload, source detail/metadata/versions/attempts/parsed viewer/original download/replacement upload/reparse/manual citation, Evidence register/detail/edit/confirmation and project search with explicit inactive inclusion. Viewer has read controls; BA edits/cites; evidence statement/confirmation is visibly distinct from requirement approval. Text is escaped by React.

## 8. Search

PostgreSQL simple full-text search with GIN index, project filters/RLS before results. All active-source versions; latest successful parse per version. Failed retry retains previous searchable knowledge. Archived/superseded excluded unless explicitly requested and labeled. Results include source/version/parse/project, filename, matched excerpt and reference. No embeddings, AI, query logging or implicit newest-wins policy.

## 9. Security/isolation

Non-owner runtime/RLS startup check now covers eight project tables. Composite FKs reject foreign lineage; raw/parsed/terminal history and evidence provenance protected by triggers/grants. Same-project scope checked for guessed source/version/parse/evidence IDs and downloads/search, including actors who belong to both projects. Forged multipart/project/actor fields, unsafe filenames, unsupported signatures/MIME/encoding, over-limit/chunked bodies and invalid quotes fail safely. Live membership rechecked after parse; revoked users cannot receive results. Audit logs actions/revision/status/error codes without raw document/query text. No delete route/public file mount/source-sharing bypass.

## 10. Executed checks

| Command/check | Exact outcome |
|---|---|
| Backend `python -m pytest -q` | **71 passed, 1 existing dependency warning, 139.50s** |
| Additional populated-Phase1 migration test, targeted pytest | **1 passed, 1 same dependency warning, 3.46s**; preserves project code/membership/audit then ingests successfully |
| Ruff check app/migrations/scripts/tests | **PASS** after formatting/import fixes |
| Alembic upgrade main0002→head and runtime grants | **PASS**, head0004_ingestion_guards |
| Alembic check | **PASS**, no new upgrade operations detected |
| Frontend `npm.cmd run typecheck` | **PASS** |
| Frontend `npm.cmd run build` | **PASS**, all source/evidence/search routes built |
| Chromium foundation cases in combined browser run | **3 passed** (individual durations2.4s/7.7s/1.3s); knowledge test initially failed on an exact-label selector |
| Chromium `npm.cmd run test:e2e -- tests/knowledge.spec.ts`, corrected locator | **1 passed, 22.4s** total (21.6s test); BA upload→three citations→search→download→version/reparse→foreign denial→VIEWER read-only |
| `Validate-Phase0.ps1` | **PASS**, all53 original SHA-256 hashes, all23 workbook sheets/cells/formulas/validations, all59 local Markdown links |

The 72 distinct backend cases include all six parsers/downloads/manual locators, three-statement demo, corruption/empty/OCR/XML/limits/formulas, exact XLSX ranges, roles/revocation/mid-parse removal, duplicate privacy, checksum tampering, immutable DB history/foreign FKs, cross-project list/read/create/update/parsed/download/search, pooled actor reset/foundation authentication and fresh/populated upgrades. Test data is synthetic and isolated in the explicit `_test` DB. Earlier development failures (permission check order and chunked413 normalization) were corrected; the final passing suite above includes them.

Existing warning: Starlette TestClient deprecates its httpx transport in favor of httpx2; the locked httpx transport still executes these tests. Browser tooling may also emit NO_COLOR/FORCE_COLOR notices, without changing assertions.

## 11. NOT RUN

Docker/Compose: Docker absent, native PostgreSQL17.11 used. Live LLM/embeddings: outside Phase2. OCR/JSON: outside chosen format scope. Production malware/OS sandbox/resource-pressure/load testing, S3 adapter, production backup/restore and real-patient privacy validation: not implemented/deployment work. No production readiness or clinical-policy approval is inferred from local tests.

## 12. Assumptions

All active project members read ordinary sources; BA/PROJECT_ADMIN edit; BUSINESS_OWNER/PROJECT_ADMIN confirm evidence only. Optional numeric confidence has no automatic authority. Search includes all active-source versions; inactive inclusion is explicit. Explicit activation is human-controlled. Supersession chains are conservatively disallowed. Limits are TECHNICAL DEFAULT — CONFIGURABLE, not clinical thresholds. English UI and accepted Phase1 identity/membership assumptions remain.

## 13. Known limitations

No OCR/AI/domain requirements/conflict engine/full trace graph/source ACL/export/job API. CSV comma-delimited logical rows; PDF text order/layout and mixed scanned pages have extraction limits; DOCX body-only and no guaranteed nested-table/header/footer/text-box coverage; XLSX formulas remain unevaluated text. Search token-based without fuzzy/stemming/accent folding/cross-section matching. Quote validation does not prove summary entailment. Subprocess timeout is not an OS sandbox or hard memory quota; compressed PDF expansion can exceed an intended memory budget. Lists/quotes/attempt viewer are bounded as documented.

## 14. Technical debt

Deployment parser hard resource/OS limits and malware review; durable leased jobs/cancellation/recovery if ingestion grows; policy-driven orphan reconciliation/retention and coordinated DB/file backup; S3 adapter; generic upload/reparse idempotency; richer DOCX/PDF fidelity and assessed multilingual retrieval; formal immutable human-confirmation/history snapshots before governance; source-specific ACL only after a policy decision; migrate TestClient transport when upstream compatibility is verified. None requires introducing AI in Phase2.

## 15. Files

Exact added/modified paths: [phase-2-files.txt](phase-2-files.txt). Application changes are in sources/evidence/knowledge/storage modules, migrations/config/grants, parser/security tests, typed frontend components/pages and browser test. Updated README and architecture/data/API/implementation/local-development docs; new ingestion/result documents. Tools, DB data, private.env, fixture credentials, caches and storage are ignored. There is no Git repository, so no commit/PR is claimed.

## 16. Phase 3 entry conditions

Review/accept Phase2, including permission/confirmation/search/supersession and extraction/resource limitations. Carry project context/RLS/composite FKs/immutable provenance tests forward. Define BA-domain register schemas/lifecycles and human authority without treating evidence classification as requirement approval. Reuse same-project stable Evidence/SourceVersion IDs. Set data/provider policy before any future AI egress; no patient data is needed. Stop here for review; do not advance automatically.
