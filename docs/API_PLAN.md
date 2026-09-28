# API contract — foundation, ingestion and future routes

## Implemented Phase 2 API

Authoritative routes/bodies/permissions/limits: [INGESTION_AND_STORAGE](INGESTION_AND_STORAGE.md). Under `/api/v1/projects/{project_id}`: sources POST multipart(file,metadata JSON)/GET, source GET/PATCH, versions POST/GET/detail, version download/parsed/parses GET and reparse POST; evidence POST/GET/detail/PATCH, evidence confirmation POST; project search GET. These paths supersede illustrative Phase 2 routes below; conflict/job/AI/approval routes remain future proposals.

All objects/files/search resolve active membership and exact project/source/version/parse lineage. BA/PROJECT_ADMIN edit; BUSINESS_OWNER/PROJECT_ADMIN confirm evidence without approving requirements. Unknown JSON/multipart fields are rejected. VersionRead derives parser state and omits storage paths. Registered parser failures return201 plus a safe result. Archived history is readable, inactive search inclusion explicit, original download audited. Accepted Origin/CSRF and safe error shape remain in force.

Phase 1 routes below and Phase 2 routes above are implemented. Remaining families are plans. DEC-MVP-001–007 and DEC-P2-001–006 control the phase boundaries. See [schema](DATA_MODEL.md), [local commands](LOCAL_DEVELOPMENT.md), and [open decisions](BASELINE_ASSESSMENT.md).

## Implemented API

Prefix `/api/v1`; errors are `{code,message,request_id}` without raw validation inputs. UUID paths and strict Pydantic request schemas reject forged actor/project/status fields. Cursor lists use `after` and `limit` (1–100), return `{items,next_cursor}`, and always scope project data. Runtime OpenAPI is available at `/docs`.

| Route | Phase 1 behavior |
|---|---|
| GET /health | Checks database connectivity; returns only service status |
| POST /auth/login | Origin-checked email/password; sets HttpOnly cookie and returns safe User, CSRF token, absolute expiry |
| GET /auth/me | Safe current User, CSRF token and expiry; rejects expired/revoked/inactive identity |
| POST /auth/logout | Origin/CSRF checked; revokes session and clears cookie |
| GET /projects | Active memberships only, cursor pagination |
| POST /projects | Active user creates project and initial PROJECT_ADMIN membership/audit atomically |
| GET /projects/{project_id} | Active membership required; my_role included |
| PATCH /projects/{project_id} | PROJECT_ADMIN, full editable context/status fields plus expected_revision; stable identifiers |
| GET /projects/{project_id}/members | Active membership; safe project-member identity/role/status fields only |
| GET /projects/{project_id}/members/{member_id} | Resolves member inside authorized project; foreign IDs return generic 404 |
| POST /projects/{project_id}/members | PROJECT_ADMIN adds provisioned active account by normalized email and canonical role |
| PATCH /projects/{project_id}/members/{member_id} | PROJECT_ADMIN changes another member's role/status with expected_revision; self-change rejected |
| GET /projects/{project_id}/audit | PROJECT_ADMIN only; bounded project-scoped safe events |

All authenticated mutations require the session cookie, explicit allowed Origin and X-CSRF-Token; login checks Origin. No bearer-token/password/approval values in project responses. Missing or inaccessible projects/members return the same 404 message; insufficient privilege within an accessible project returns 403. No global user-list, signup, AI or requirement-approval endpoint exists. Ingestion is implemented in Phase 2. Account bootstrap/provisioning is operator CLI only.

Roles replace the provisional names below: ADMIN → PROJECT_ADMIN, BUSINESS_REVIEWER → BUSINESS_OWNER, TECH_REVIEWER → TECH; QC is explicit. Global system-admin status grants no project permissions. All active roles can read project context/member register; only PROJECT_ADMIN manages other members/settings or reads audit. Future BA/Business/Medical gates follow DEC-MVP-002, not project administration status.

Project/context histories, stakeholders, multi-role membership, idempotency keys and later domain routes remain deferred. Current project/member writes use revision checks, project-level administration locks and transactional audit; duplicate memberships return 409. These are recorded limitations, not completed API-plan features.

## Contract conventions

Base `/api/v1`. Project routes below use `P = /api/v1/projects/{project_id}`. Resolve project access before object lookup. Request bodies never control actor/approval identity. UUIDs are API identifiers; display codes are presentation fields. All endpoints, including file download, jobs, reverse trace and evaluation, check authorization. Global login/project-list endpoints expose only the caller's authorized scope.

Use strict Pydantic request/response schemas with forbidden unknown fields for mutations. Enum classifications, domain kind, lifecycle and review outcome are separate fields. PATCH changes permitted draft metadata/content only; `status`, `approved_by`, `project_id` and baseline pointers are not writable there. Content edits append versions. `expected_revision`/If-Match prevents stale writes. Do not echo sensitive request bodies in validation failures.

Lists return `{items,next_cursor}` with stable ordering and bounded page size. Mutations return the resource and its revision. Long operations return `202 {job_id,status_url}`; clients poll authorized jobs and fetch typed results. POST creates use idempotency keys where repeat submission could duplicate jobs, uploads, promotions, approval/baseline or changes. Key scope includes project, actor, route and body hash; conflicting reuse returns 409. Size/time/token bounds are deployment-configured (A12).

Errors: 401 unauthenticated; 403 insufficient capability in an accessible project; 404 absent/inaccessible project or object; 409 invalid transition, stale version, unresolved conflict/gate or idempotency mismatch; 413 over upload limit; 415 unsupported format; 422 invalid contract/unsupported references; 429 resource limit; 503 provider/storage unavailable. Sanitized errors have `{code,message,request_id,details}`. Approval gate errors may include accessible blocking question/review IDs. Inaccessible foreign references never disclose their private metadata.

## Proposed capability matrix

All cells require active project membership. **ASSUMPTION — NEEDS CONFIRMATION (A04/A05/A11/A14):** multiple roles, self-approval separation, membership-grant authority, gate assignments, post-baseline progression and export rights need policy decisions before implementation.

| Role/capability | Read | Draft/analyze | Review | Approve/baseline | Membership |
|---|---|---|---|---|---|
| BA | Project data | Yes | BA quality gate | No business/clinical approval; baseline only if separately authorized | Only explicit project-admin capability |
| BUSINESS_OWNER | Project data | Attributed answers/decisions within authority | Business gate | Business approval after all required gates | No |
| MEDICAL_SME | Project data | Clinical confirmations/answers | Medical gate | Clinical clearance only; not substitute Business approval | No |
| TECH | Project data | Assigned technical confirmations | Tech gate | No business/clinical approval | No |
| VIEWER / QC | Project data | No | No formal approval; UAT evidence recording needs an explicit capability | No | No |
| PROJECT_ADMIN | Own project through active membership | Project settings/members in Phase 1 | No implicit domain authority | No implicit approval | Project administration |
| Assigned Security/Compliance/Finance gate | Within membership | Assigned confirmations | Only assigned gate | No substitute Business/Medical authority | No |
| AI / worker | Only authorized job inputs | Proposed drafts through internal service only | Never human review | Never | Never |

No endpoint lets an actor grant itself business/medical approval authority. Bootstrap and grant authority must be resolved in Phase 1. All create/update/review/approve/reject/baseline/supersede/change/export/permission mutations produce project audit; unauthenticated login attempts go to separate platform security events.

## Endpoint families

| Method and route | Input / output and rules | Phase |
|---|---|---:|
| POST `/auth/login`; POST `/auth/logout`; GET `/auth/me` | Provisioned identity → session; generic credential error, revocation, rate controls | 1 |
| GET/POST `/projects` | List own projects / create project and initial membership atomically | 1 |
| GET/PATCH `P` | Context metadata, owners, scope and revision; audit changes | 1 |
| GET `P/context`; GET `P/context/history` | Exact context preview for analysis and prior revisions | 1 |
| GET/POST `P/members`; PATCH `P/members/{id}` | Membership/role changes via explicit administrator capability; audit and revoke affected access | 1 |
| GET/POST `P/stakeholders`; GET/PATCH `P/stakeholders/{id}` | Named actors, authority description and optional linked member | 1 |
| GET/POST `P/sources` | Metadata or pasted text registration; text preserved as original source version | 2 |
| POST `P/sources/upload` | Multipart raw file + metadata → registered source/version and parse job; checksum | 2 |
| GET `P/sources/{id}`; GET `P/sources/{id}/versions` | Source/current version, parser state/errors, evidence summary/history | 2 |
| POST `P/sources/{id}/versions` | New immutable upload/text version; never overwrite previous bytes | 2 |
| GET `P/sources/{id}/versions/{version_id}/download` | Authorized raw original; opaque filename, no storage credentials/path exposure | 2 |
| POST `P/sources/{id}/parse`; POST `P/sources/{id}/archive` | Retry registered version / authorized archive; preserve history | 2 |
| POST `P/sources/{id}/supersede` | Explicit replacement source ID and rationale; validate project, authority, cycles and impact | 2/5 |
| GET/POST `P/evidence`; GET `P/evidence/{id}` | Exact source/version/location/extract and classification; validate references | 2 |
| POST `P/evidence/{id}/confirm` | Attributed human confirmation, target content hash, authority; no synthetic reviewer | 3/5 |
| GET `P/conflicts`; POST `P/conflicts/{id}/resolve` | Human resolution decision/citations; no auto-resolution by recency | 2/5 |
| GET/POST `P/questions`; GET/PATCH `P/questions/{id}` | Text/priority/assignee/due date, visible blocker references | 3 |
| POST `P/questions/{id}/answers` | Attributed answer + source/evidence or confirmation, expected_revision → ANSWERED | 3 |
| POST `P/questions/{id}/close`; POST `P/questions/{id}/cancel` | Authorized validation/reason; cancellation cannot silently satisfy a blocking gap | 3 |
| GET/POST `P/assumptions`; GET/PATCH `P/assumptions/{id}` | Distinct unconfirmed assertion and risk; edits auditable | 3 |
| POST `P/assumptions/{id}/confirm`; POST `.../reject`; POST `.../supersede` | Human confirmation/reason/replacement, retained origin | 3/5 |
| GET/POST `P/decisions`; GET/PATCH `P/decisions/{id}` | PROPOSED decision, maker, reason, provenance; active text immutable | 3 |
| POST `P/decisions/{id}/activate`; POST `.../supersede`; POST `.../revoke` | Authorized human decision; atomic replacement; audit | 3/5 |
| GET/POST `P/risks`; GET/PATCH `P/risks/{id}`; POST `.../transition` | Risk register, mitigation and authorized status command | 3 |
| GET/POST `P/business-rules`; GET/PATCH `P/business-rules/{id}`; POST `.../transition` | Draft revisions, provenance and governance; no AI approval | 3/5 |
| GET/POST `P/requirements`; GET `P/requirements/{id}` | Create DISCOVERED/DRAFT; return current approved, baseline and working pointers separately | 3 |
| PATCH `P/requirements/{id}`; GET `.../versions`; GET `.../versions/{version_id}` | New content revision/history; reject protected content change without required CR | 3/5 |
| POST `P/requirements/{id}/transition` | Allowed non-approval transition, expected revision, reason/evidence | 3/5 |
| GET/POST `P/requirements/{id}/versions/{version_id}/acceptance-criteria` | Version-specific AC; supported rules only; material edits invalidate reviews | 3 |
| GET/POST `P/requirements/{id}/versions/{version_id}/user-stories` | Supported actor/capability/value | 3 |
| GET/POST `P/{register}`; GET/PATCH `P/{register}/{id}` | Concrete register schemas: data-dictionary, role-permissions, integrations, nfr, glossary, regulations, action-items, uat-scenarios; immutable reviewed revisions and trace links | 3 |
| POST `P/uat-scenarios/{id}/results` | Minimal attributed UAT evidence/sign-off; no automated release | 6/10 |
| POST `P/analysis-runs` | Type REQUIREMENT/MEETING/REVIEW, request/source IDs, context revision, prior run; → job/run | 4 |
| GET `P/analysis-runs`; GET `P/analysis-runs/{id}` | Structured dimensions/items, validation findings, used sources and review state | 4 |
| POST `P/analysis-runs/{id}/promotions` | Selected item IDs → idempotent domain drafts/proposed decisions and provenance | 4 |
| POST `P/analysis-runs/{id}/feedback` | CORRECT/NEEDS_REVISION/UNSAFE/UNSUPPORTED with human attribution | 4/9 |
| POST `P/review-requests`; GET `P/review-requests` | Target version, required gate/assignee; only authorized assignment | 5 |
| POST `P/reviews`; GET `P/requirements/{id}/reviews` | Human outcome bound to version/content/dependencies and gate capability | 5 |
| POST `P/requirements/{id}/approve`; POST `.../reject`; POST `.../baseline` | Separate human commands; recheck all mandatory gates/provenance/blockers atomically | 5 |
| POST `P/requirements/{id}/supersede`; POST `.../deprecate` | Explicit replacement/reason and approved CR if required; old content retained | 5/7 |
| GET/POST `P/trace-links`; POST `P/trace-links/{id}/supersede` | Typed node/relation validation; no dangling or foreign endpoints | 6 |
| GET `P/trace-nodes/{id}/neighbors?direction=in\|out\|both`; GET `P/trace-health` | Bounded navigation and stale/broken/missing support findings | 6 |
| GET/POST `P/change-requests`; GET/PATCH `P/change-requests/{id}` | Old version targets, reason/requester/priority; audit edits | 7 |
| POST `P/change-requests/{id}/impact-analyses`; GET `.../impact-analyses` | Graph snapshot and AI-assisted draft impact job; return path evidence and gaps | 7 |
| POST `P/impact-analyses/{id}/confirm` | Human dispositions for impact items; pin confirmed graph/version snapshot | 7 |
| POST `P/change-requests/{id}/approve`; POST `.../reject` | Authorized human decision referring to confirmed impact revision | 7 |
| POST `P/change-requests/{id}/apply` | Idempotent replacement draft creation; reject stale target/impact; never approve new draft | 7 |
| GET `P/artifacts`; POST `P/artifacts` | Artifact kind, DRAFT/OFFICIAL, format, selected scope/CR; → job with pinned input selection | 8 |
| GET `P/artifacts/{id}`; GET `.../download`; GET `.../inputs` | Immutable artifact version, status/labels, authorized export and provenance manifest | 8 |
| GET/POST `P/evaluation-cases`; GET `.../{id}` | Versioned expected/forbidden synthetic behavior, role restrictions | 9 |
| POST `P/evaluation-runs`; GET `.../{id}` | Execute case revisions, preserve actual results/provider/prompt/knowledge versions | 9 |
| GET/POST `P/ai-incidents`; GET/PATCH `P/ai-incidents/{id}` | Incident lifecycle and regression-case references; restricted sensitive details | 9 |
| GET `P/audit`; GET `P/jobs/{id}`; POST `P/jobs/{id}/cancel` | Authorized history, durable job status/result, safe cancellation | 1/2 onward |

Register notation above groups documentation only: each resource will have its own schema and service. It is not a generic writable object endpoint. Non-approval transitions and terminal states use an explicit backend allowlist, not arbitrary enum assignment. No public audit edit/delete route. No cross-project AI search route.

## Example command semantics

Analysis request (IDs are schematic, actual contract uses UUIDs):

```json
{
  "analysis_type": "REQUIREMENT",
  "request": "Phòng khám muốn cho phép bệnh nhân hủy lịch khám.",
  "source_version_ids": ["<authorized-source-version-uuid>"],
  "context_revision_id": "<context-revision-uuid>"
}
```

Output items include `classification`, `content`, `rationale`, `source_refs`, `evidence_refs`, `requires_human_review`, and `clinical_review_required`; requirements/rules/AC are typed draft proposals. Missing actors/status/payment policy creates questions. No caller-supplied approval flags are accepted.

Approval command body: `{version_id, expected_revision, review_ids, reason}`. Backend derives actor and authority, locks version, rechecks reviews against content/dependency hash, checks support/blockers/clinical gate, then emits lifecycle/audit events. Reusing a review from another version/project returns an error without changing the requirement.

CR apply body: `{confirmed_impact_analysis_id, target_versions, expected_revision}`. Backend checks approved CR, exact old baseline/approved targets and confirmed impacts; creates DRAFT successors and trace links. A second identical command returns the existing result. Approval of the CR never implies approval of successor content.

## Frontend route plan

`/login`, `/projects`, `/projects/[projectId]`, then project-relative `/context`, `/sources`, `/sources/[sourceId]`, `/evidence`, `/analyze`, `/analysis/[runId]`, `/questions`, `/assumptions`, `/requirements`, `/requirements/[requirementId]`, `/decisions`, `/risks`, `/business-rules`, `/traceability`, `/changes`, `/changes/[changeId]`, `/artifacts`, `/glossary`, `/regulations`, `/audit`, `/evaluations`.

Data/permission/integration/NFR registers can be panels linked from requirements/context; impact analysis is a CR detail panel. Prioritize a coherent workflow over separate elaborate screens. All draft/unknown/conflict/clinical-gate labels and version pointers must remain visible. API supplies allowed actions and missing gates for usability while still enforcing every action independently.

## Contract test plan

Phase 1 generates OpenAPI and tests auth/membership plus unknown-field rejection. Later tests cover valid and forged linked IDs, inaccessible downloads/jobs/exports, stale writes, illegal transitions, AI actor approval denial, human approval without support, unresolved blocking/conflicting information, required clinical review, version-stale reviews, idempotent retries, supersession cycles, baseline mutation denial and provider failures. Component/browser tests ensure users can complete the workflow without manual DB changes. No API test is reported as passing in Phase 0.
