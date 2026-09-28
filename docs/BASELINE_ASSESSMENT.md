# Baseline assessment and decision register

Inspected 2026-09-28. Original files remain unchanged. Source paths below refer to the original kit; workbook addresses are exact evidence locations. All proposals extending unspecified policy are explicitly marked **ASSUMPTION — NEEDS CONFIRMATION**. They are not new approved product requirements.

## Accepted Phase 1 decisions

The user's Phase 1 instruction accepts Phase 0 and locks the following; these supersede the corresponding earlier assumptions, without rewriting original kit references:

| Decision | Locked interpretation |
|---|---|
| DEC-MVP-001 | Application-local normalized email/password; secure hashes; stable User identity can support external IdP later |
| DEC-MVP-002 | AI has no approval authority; BA reviews, Business Owner final business approval; mandatory Medical SME review when clinical flag is true; approve/reject audited in later governance phase |
| DEC-MVP-003 | Active ProjectMembership is mandatory; backend/repository project scope authoritative |
| DEC-MVP-004 | All listed private domain records require authorized project membership; permitted audit also scoped |
| DEC-MVP-005 | Provider abstraction; synthetic/non-patient development/tests; no live AI needed in Phase 1 |
| DEC-MVP-006 | Formal CR mandatory after BASELINED; before baseline controlled editing/versioning permitted; historical versions never mutated |
| DEC-MVP-007 | clinical_review_required defaults false; clinical-impact analysis may flag true, routing mandatory human SME review |

Canonical project roles are PROJECT_ADMIN, BA, BUSINESS_OWNER, MEDICAL_SME, TECH, QC, VIEWER. Global system-admin status is separate. Phase 1 implements no requirement approval or clinical-analysis workflow.

Remaining foundation interpretations are **ASSUMPTION — NEEDS CONFIRMATION**: any active local user may create a project; creator gets PROJECT_ADMIN; each membership currently has one role; project administrators manage other members but cannot change their own membership; operator CLI provisions accounts using migration credentials; session lifetime is eight hours and single-process login limit is 10/IP/account per 300 seconds; UI is English. These are reversible technical/permission defaults, not additional clinical scope.

## Inspection coverage

| Directory / file | Material inspected and design consequence |
|---|---|
| `00_START_HERE/` | Blueprint, principles, quick start, IDs/version conventions; human ownership and protected history |
| `01_Project_Setup/` | Formal scope, charter, context, stakeholders, YAML; MUST/SHOULD/OUT, actors, conditional gates |
| `02_Knowledge_Base/` | Ingestion, glossary, regulations, source-of-truth rules; explicit conflict resolution and supersession |
| `03_Elicitation/` | Intake, meeting, questions; classifications, answers, action items |
| `04_Analysis/` | All eight templates; As-Is/To-Be, rules, data, permissions, integration, NFR, clinical risks |
| `05_Requirements/` | Specification, story/AC, review checklist; provenance and complete review scope |
| `06_Governance/` | Evidence, assumption, decision, human gates; exact citations and authority |
| `07_Traceability_Change/` | RTM, CR, impact; version-aware graph and baseline control |
| `08_Test_UAT/` | UAT and solution evaluation; scenario draft and future feedback, no QC replacement |
| `09_AI_Governance/` | Guardrails, security/privacy, evaluation, incidents; boundary controls and regressions |
| `10_Artifacts/` | Index and generation checklist; selectable packages and approved inputs |
| `11_Master_Tracker/` | All 23 sheets, populated rows, seven dashboard formulas and validation lists |
| `12_AI_Prompts/` | All five templates; concise structured rationale, no new policy or autonomous approval |
| `13_Example/` | Receptionist cancellation scenario; illustrative rather than universal policy |
| `14_Development/` | README, 12 epics, DoD; MUST coverage and release readiness |
| `manifest.json` | v1.1-development-scope package references Conceptual Blueprint V1.0 and Scope v1.0 |

The [JSON snapshot](baseline-inspection.json) records all original file hashes and workbook cell contents/formulas/validations. Reproduce with `powershell -NoProfile -File scripts/Inspect-Baseline.ps1` from the workspace root. Reading XML does not execute workbook formulas. Dashboard cached values match the visible sample counts; they are not live product metrics.

## Workbook structure and schema mapping

Most register sheets have a title in row 1, template guidance in row 2, headers in row 4, and examples from row 5. Dashboard and Development_Scope use custom layouts. No relational FK constraints exist in the spreadsheet; validation lists only restrict selected cells, generally through row 500.

| Sheet | Populated business rows | Planned representation |
|---|---:|---|
| Dashboard | 7 KPI formulas | Optional project-scoped aggregate view, never imported as facts |
| Project | 1 | Project and context revision |
| Sources | 1 | Source, SourceVersion |
| Stakeholders | 1 | Stakeholder, optional User association |
| Requirements | 9 | Requirement, RequirementVersion, reviews, provenance links |
| Evidence | 1 | Evidence tied to immutable SourceVersion |
| Questions | 1 | Question, QuestionAnswer, HumanConfirmation |
| Assumptions | 1 | Assumption and attributed confirmation |
| Decisions | 1 | Decision and supersedes relationship |
| Risks | 1 | Risk |
| Business_Rules | 1 | BusinessRule and revisions |
| Data_Dictionary | 1 | DataDictionaryEntry (field definitions, not patient rows) |
| Roles_Permissions | 1 | RolePermission (analyzed business permissions, separate from RBAC) |
| Integrations | 1 | Integration and mapping details; no live integration connector |
| NFR | 1 | Requirement(type=NFR) plus NFRDetail; legacy NFR code retained |
| Traceability | 1 | TraceLink and RequirementRelation projection |
| Change_Requests | 1 | ChangeRequest, affected nodes, ImpactAnalysis, ImpactItem |
| UAT | 1 | UATScenario, minimal UATResult/sign-off |
| Glossary | 1 | GlossaryTerm |
| Regulations | 1 | Project-scoped RegulationReference |
| AI_Evaluation | 1 | Project-scoped AIEvaluationCase and separate executions |
| AI_Incidents | 1 | AIIncident tied to evaluation/regression |
| Development_Scope | 12 epics, 10 OUT summaries, 8 DoD summaries | Planning reference, not runtime project data |

Detailed column names and validation values are preserved without abbreviation in the snapshot. The proposed schema normalizes workbook `Related_ID`, `Affected_Items`, single source/evidence cells and reviewer-name strings into typed relationships and attributable records. Workbook import/synchronization is not a new MVP capability: XLSX ingestion extracts source content; automated migration of this tracker into live objects would require a separately reviewed mapping.

## Conflicts, gaps and dispositions

| ID | Evidence | Finding | Phase 0 disposition |
|---|---|---|---|
| C01 | Scope §13 vs user's §29–30 | Baseline calls implementation foundation “Phase 0”; user requests assessment only | User's numbering 0–10 governs; foundation begins Phase 1 |
| C02 | `Human_Review_Gate.md` final sentence vs scope critical rules and user Rule 4 | Conditional wording could imply an AI approval exception | No exception: AI cannot approve under any project policy |
| C03 | YAML `clinical_review_required: true`; scope journey step 13; example §8 | Blanket project flag versus conditional clinical gate | Resolved by DEC-MVP-007: default false, flagged clinical impact requires SME |
| C04 | YAML `latest_approved_supersedes_old`; source-of-truth rules 2/4; README rule 5 | “Latest” may be mistaken for automatic conflict resolution | Recency is metadata. Only explicit authorized replacement supersedes; otherwise unresolved conflict |
| C05 | Workbook Project!A5, Stakeholders!B5 and most register B5 cells | Only `PRJ-MBAAI-001` exists; many samples use missing `PRJ-001` | Samples are not import-ready; reject unresolved project/record links; no automatic remapping |
| C06 | Requirements!A5:A13 vs Questions!C5, Decisions!I5, Traceability!D5:G5 | Legacy `REQ-001`/`SRC-001`/`EVD-001` references are absent | Preserve original examples; build fresh synthetic fixtures later with valid references |
| C07 | Regulations!A4:J4, AI_Evaluation!A4:L4 | No `Project_ID` column | Runtime project records require project_id; no shared private evaluation/regulation store |
| C08 | Requirements!H5:M13; Business_Rules!F5:J5; naming guide | Draft records labeled `1.0`, guide uses `0.x` drafts and `1.0` baseline | Preserve legacy label as metadata if ever imported; label alone is never approval |
| C09 | Requirements!I4:I13 and Evidence!I5 | Single review status and free-text confirmed-by cannot prove multi-gate authority | Separate version-specific reviews and HumanConfirmation; imported text is not authenticated approval |
| C10 | Scope §7, workbook columns | Missing auth, versions, source versions, explicit human confirmation, AC, artifact inputs, audit/run records | Supporting tables needed; schema specifies them without treating blanks as completed features |
| C11 | Scope EPIC-10, artifact index, user §19 | Different artifact lists and detail levels | Preserve combined required outputs using shared templates; optional DOCX export; not all 20 package documents mandatory |
| C12 | Example §1 vs user's demo | Receptionist acts vs patient cancellation request | Record raw request; ask who may cancel before drafting permission rules |
| C13 | Quick start/ingestion/meeting prompts vs seven-class enum | ACTION / ACTION ITEM / ACTION_ITEM; REQUIREMENT appears among output categories | Canonical ACTION_ITEM; distinguish information classification from proposed domain entity |
| C14 | AI evaluation template vs workbook AI_Evaluation!G5 | Template omits NOT_RUN; workbook includes it | NOT_RUN execution status supported; not a pass |
| C15 | Scope DoD step 16 vs critical rule 10 / user Rule 8 | CR described for approved change as well as after baseline | Resolved by DEC-MVP-006: CR mandatory after BASELINED; controlled new versions before baseline |
| C16 | Roles list vs Tech/Security/Compliance gate and example Finance review | Security/Compliance/Finance lack dedicated app roles | A04: explicit review assignments; no automatic mapping to admin/tech authority |
| C17 | Development_Scope sheet summaries vs formal scope | Summaries omit detail; requirements sample has nine entries for eleven MUST epics | Formal scope/backlog/DoD govern; sample row count does not reduce scope |

## Assumptions and open decisions

This is the original Phase 0 assumption register with Phase 1 resolutions annotated. Unresolved parts remain **ASSUMPTION — NEEDS CONFIRMATION**; the accepted decisions above are authoritative.

| ID | Proposed default or unresolved choice | Owner / needed by |
|---|---|---|
| A01 | Local email/password locked by DEC-MVP-001; revocable cookie session implemented. No public signup/SSO in Phase 1; future deployment IdP remains open | Product/Security |
| A02 | Clinical default/gate resolved by DEC-MVP-007/002. Who may clear a false-positive flag remains open for governance | BA/Medical SME, Phase 5 |
| A03 | Resolved: DEC-MVP-006 mandates CR after BASELINED only; immutable historical versions always | Business/BA |
| A04 | Seven canonical roles locked. One role per membership implemented; system admin no project bypass; project admins assign other members. Future gate-specific grants and self-approval separation remain open | Product/Security/Business, Phase 5 |
| A05 | Earlier BA-plus-admin proposal replaced by creator PROJECT_ADMIN only. This grant default remains an explicit foundation assumption; no implicit Business/Medical authority | Product/Security |
| A06 | Project membership boundary locked by DEC-MVP-004. No restricted-source ACL implementation in Phase 1; additional within-project restrictions would require a later policy decision | Security/BA, Phase 2 |
| A07 | UUID internal IDs plus project-local display codes; append-only content revisions with separate lifecycle events, compare-and-swap writes; backend-controlled API workflow | Architect, Phase 1–3 |
| A08 | Local storage first; PostgreSQL jobs with worker from the same codebase; lexical retrieval first, pgvector only when evaluated as needed; no separate broker/vector DB | Architect, Phase 2–4 |
| A09 | Provider, model, embeddings, approved hosting region/data egress, retention and redaction policies remain TBD; no external document submission until deployment policy is selected | Product/Security, Phase 4 |
| A10 | Product UI language and bilingual search/evaluation behavior: baseline is Vietnamese, examples/prompts also English; preserve Unicode, language choice remains open | Product/BA, Phase 1–4 |
| A11 | Lifecycle backtracking, rejection origins, baseline authority, replacement activation timing, question cancellation authority and risk acceptance authority are not fully specified | BA/Business, Phase 3–5 |
| A12 | Upload/parser/AI time, size, token and concurrency bounds are configurable technical controls; exact values, SLA, RPO/RTO and evaluation acceptance thresholds remain TBD | Tech/Security/Product, before respective phase/release |
| A13 | UI exposes single-item baselining initially; multi-item release baseline packages and long-form chat are not required. Analysis reruns keep linked history | Product/BA, Phase 5 |
| A14 | Official logs may report current open questions/risks as such, but specifications only assert approved policy. Artifact review/publishing authority and export permission need agreement | BA/Business/Security, Phase 8 |
| A15 | Safe first-admin CLI bootstrap/provisioning implemented. Production deletion/retention, legal holds, backups and incident escalation remain deployment decisions | Security/Operations, Phase 9–10 |

No numeric business rule, provider, hosting jurisdiction or legal conclusion has been inferred from the baseline. These questions need decisions before dependent implementation, not before finishing Phase 0 documentation.

## Risks

| Risk | Mitigation / verification |
|---|---|
| Template examples accidentally become business truth | No seed/import from workbook; validate project references and preserve provenance |
| Project leakage via files, cache, retrieval, workers or exports | One authorized context; DB constraints/RLS; reauthorize jobs/downloads; adversarial cross-project tests |
| Schema-valid AI output still contains unsupported policy | Semantic provenance checks, review gates, negative golden cases; no claim that JSON validation proves truth |
| Changed content keeps stale approval | Reviews bind content hash/version; new content invalidates gates; concurrent approval/edit tests |
| “Latest” content destroys baseline or conceals conflict | Explicit replacement, version-pinned artifacts, immutable baseline, conflict records |
| Parsing loses exact citations or workbook formulas are executed | Version-specific location metadata, parser errors retained, cached formula text only, no macro execution |
| Production readiness inferred from local demo | Separate security/privacy/backup and quality release gates; synthetic development data |
| Runtime setup blocks Phase 1 | Install/verify approved Python and PostgreSQL/container tooling and lock compatible dependencies in Phase 1 |
