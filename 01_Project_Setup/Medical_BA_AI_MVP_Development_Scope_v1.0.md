# Medical BA AI — MVP Development Scope v1.0

**Baseline:** Medical BA AI — Final Conceptual Blueprint V1.0  
**Purpose:** Chốt phạm vi đủ rõ để Product/BA/Tech bắt đầu thiết kế chi tiết và code MVP.  
**Status:** Development Baseline  
**Scope principle:** MVP phải chứng minh được một vòng đời BA end-to-end có source/evidence, human review và traceability; không tự động hóa quyết định lâm sàng hay ghi dữ liệu vào hệ thống bệnh viện production.

---

## 1. Product Goal

Xây dựng một **Medical Business Analyst Copilot** giúp BA trong domain y tế:

1. Tạo workspace riêng cho từng project/module.
2. Nạp và quản lý nguồn thông tin dự án.
3. Trích xuất và phân loại thông tin thành FACT / ASSUMPTION / QUESTION / DECISION / RECOMMENDATION / RISK / ACTION ITEM.
4. Phân tích request theo BA framework và healthcare checklist.
5. Phát hiện thông tin thiếu, mâu thuẫn và sinh BA questions.
6. Tạo draft requirement có trace về Source/Evidence.
7. Quản lý lifecycle của Requirement / Decision / Question / Risk.
8. Cho BA/Business/Medical SME review và approve theo đúng quyền.
9. Thực hiện traceability và impact analysis ở mức MVP.
10. Sinh bộ artifact BA từ thông tin hiện hành đã được review/approve.

AI **không sở hữu requirement** và không tự approve business/clinical/technical decision.

---

## 2. Primary Users

| Actor | Vai trò trong MVP |
|---|---|
| BA | User chính; tạo project, nạp nguồn, phân tích, chỉnh sửa, trace, tạo artifact |
| Business Owner / Product Owner | Review và approve business requirement/decision |
| Medical SME | Review các requirement có Clinical Impact |
| Tech Lead / Architect | Review integration/NFR/technical-impact items khi được assign |
| QC | Đọc requirement/AC và sử dụng output cho test/UAT; không phải user chính ở MVP |
| System Admin | Quản lý user/role/workspace cơ bản |

---

## 3. MVP End-to-End User Journey

```text
Login
  ↓
Create Project Workspace
  ↓
Define Project Context / Scope / Stakeholders
  ↓
Upload or paste Source
  ↓
Register Source + Extract Evidence
  ↓
Run Requirement Analysis
  ↓
FACT / ASSUMPTION / QUESTION / DECISION / RISK classification
  ↓
Gap & Conflict Detection
  ↓
BA answers / records human confirmation
  ↓
Generate Draft Requirements + Rules + AC + Risks
  ↓
Human Review Gate
  ↓
Approve / Baseline
  ↓
Trace Source → Evidence → Requirement → AC
  ↓
Change Request / Impact Analysis when changed
  ↓
Generate BA Artifact Package
```

---

## 4. In Scope — MVP

### EPIC-01 — Authentication, User & Workspace Isolation — MUST

**Capability**
- Login/authentication.
- User identity and basic roles.
- Create/view/update Project Workspace.
- Project ID is mandatory for project data.
- Data of Project A must not be used to answer Project B unless explicitly authorized later.

**Minimum roles**
- ADMIN
- BA
- BUSINESS_REVIEWER
- MEDICAL_SME
- TECH_REVIEWER
- VIEWER

**Acceptance baseline**
- User without project access cannot read project content.
- Every stored project object contains Project ID.
- AI retrieval is scoped to current Project ID.

---

### EPIC-02 — Project Setup & Context — MUST

**Capability**
- Project name, organization, module, business owner, BA owner.
- Scope / Out of Scope.
- Stakeholders.
- Current systems / downstream systems.
- Project glossary.

**Acceptance baseline**
- AI can show the project context being used before analysis.
- Project scope can be edited with audit history.

---

### EPIC-03 — Knowledge Ingestion & Source Registry — MUST

**MVP input types**
- Plain text / pasted meeting transcript.
- TXT / Markdown.
- PDF with extractable text.
- DOCX.
- XLSX/CSV for structured BA information.

**Optional if low effort**
- Image/screenshot attachment for reference only.

**Not required in MVP**
- OCR-heavy scanned document pipeline.
- Audio transcription.
- Live email/chat/calendar ingestion.

**Capability**
- Upload/register source.
- Source metadata: ID, type, name, date, owner, trust level, status.
- Keep original source reference.
- Chunk/index source for retrieval.
- Mark source ACTIVE / SUPERSEDED / ARCHIVED.

**Acceptance baseline**
- User can identify exactly which source was used by an AI analysis.
- A superseded source is not silently treated as current truth.

---

### EPIC-04 — Evidence & Source of Truth — MUST

**Capability**
- Create Evidence record linked to Source.
- Save exact reference: page/section/line/timestamp where available.
- Evidence classification.
- Conflict detection across sources.
- Source-of-truth status and supersede relationship.

**Core rule**

```text
NO SOURCE + NO HUMAN CONFIRMATION
= DO NOT PRESENT AS FACT
```

**Acceptance baseline**
- Every approved requirement has at least one Source/Evidence or explicit Human Confirmation record.
- If two active sources conflict, AI flags CONFLICT and does not silently choose one.

---

### EPIC-05 — Medical BA Analysis Engine — MUST

**Input**
- Raw request, meeting content or selected source(s).

**Minimum analysis output**
- Business Need.
- Actors / Stakeholders.
- Requirement classification.
- Facts / Decisions / Assumptions.
- Missing information.
- Blocking / important questions.
- As-Is summary when evidence exists.
- To-Be draft only when requested/appropriate.
- Business Rules.
- Data considerations.
- Role / Permission considerations.
- Integration/API considerations.
- Exception / edge cases.
- NFR considerations.
- Risks.
- Clinical Safety flags.
- Privacy / Security / Regulatory flags.
- Draft Requirement.
- Draft Acceptance Criteria.
- Human review required.

**Healthcare checklist minimum**
- Patient identification.
- Encounter/appointment context when applicable.
- Clinical status/state.
- Role/authorization.
- Audit/history.
- Downstream impact: pharmacy/lab/imaging/billing/inventory/notification where relevant.
- Sensitive health data exposure.

**Acceptance baseline**
- AI labels assumptions instead of presenting them as requirements.
- AI does not invent SLA/time window/threshold/clinical rule.
- Clinical-impact items are flagged for Medical SME review.

---

### EPIC-06 — Questions, Decisions, Assumptions & Risks — MUST

**Capability**
- CRUD and lifecycle for Question.
- Record Answer and Answer Source.
- CRUD and lifecycle for Decision.
- Decision can supersede an older Decision.
- CRUD and lifecycle for Assumption.
- CRUD and lifecycle for Risk.
- Relationship to Requirement/Source/Evidence.

**Acceptance baseline**
- Blocking question remains visible until answered/closed.
- Active decision supersedes old decision only through an explicit relationship/status change.

---

### EPIC-07 — Requirement Management & Human Review — MUST

**Requirement types**
- BUSINESS
- STAKEHOLDER
- FUNCTIONAL
- NFR
- TRANSITION

**Lifecycle**

```text
DISCOVERED
→ DRAFT
→ UNDER_ANALYSIS
→ WAITING_BUSINESS
→ CONFIRMED
→ APPROVED
→ BASELINED
→ IMPLEMENTED
→ VERIFIED
→ RELEASED
```

Additional terminal/replacement states:
- REJECTED
- SUPERSEDED
- DEPRECATED

**Human review gates**
- BA review: analysis quality.
- Business review: business requirement/decision.
- Medical SME review: clinical-impact requirement.
- Tech/Security review: when tagged as required.

**Acceptance baseline**
- AI cannot set APPROVED on its own.
- Requirement change history is auditable.
- Approved version is distinguishable from draft/latest editing version.

---

### EPIC-08 — Traceability & Requirement Graph — MUST

**Minimum node types**
- SOURCE
- EVIDENCE
- DECISION
- REQUIREMENT
- BUSINESS_RULE
- QUESTION
- RISK
- ACCEPTANCE_CRITERIA
- ARTIFACT

**Minimum relations**
- SUPPORTS
- DERIVED_FROM
- ANSWERS
- SUPERSEDES
- IMPLEMENTS
- VALIDATES
- AFFECTS

**Acceptance baseline**
- User can start from a Requirement and see its Source/Evidence.
- User can start from a changed Requirement and identify directly linked downstream items.
- Broken trace is visible.

---

### EPIC-09 — Change Request & Impact Analysis — MUST

**Capability**
- Create Change Request.
- Link changed requirement/decision/rule.
- AI identifies affected trace nodes.
- Produce draft impact summary.
- Human confirms impact before applying change to baseline.

**MVP impact areas**
- Requirements.
- Business Rules.
- Data.
- Roles/Permissions.
- Integration/API.
- Acceptance Criteria.
- BA artifacts.

**Acceptance baseline**
- Baseline content is not silently overwritten after an approved change request.

---

### EPIC-10 — Artifact Generation — MUST

**MVP artifacts**
- Requirement Analysis summary.
- Requirement Specification.
- User Story + Acceptance Criteria.
- Question Log.
- Decision Log.
- Risk Register.
- Data Dictionary summary.
- Role/Permission Matrix summary.
- API/Integration inventory summary.
- Traceability Matrix.
- Change Impact Report.
- UAT scenario draft.

**MVP export formats**
- On-screen structured view.
- Markdown/text export.
- XLSX export for tracker/tabular artifacts.
- DOCX export is SHOULD if implementation cost is reasonable; otherwise V1.1.

**Acceptance baseline**
- Official artifact uses current approved/baselined information by default.
- Draft/unapproved content must be visibly labeled if included.

---

### EPIC-11 — AI Guardrails, Audit & Evaluation — MUST

**Guardrails**
- Project isolation.
- Prompt injection defense: source content is data, not system instruction.
- No assumption → fact conversion.
- No autonomous approval.
- No clinical diagnosis/treatment/medication decision.
- No final legal/compliance conclusion.

**Audit**
- Who performed action.
- Object affected.
- Timestamp.
- Old/new value for important lifecycle changes.
- AI model/prompt version for generated analysis when available.
- Source IDs used.

**Evaluation**
- Golden test cases for hallucination, conflict, clinical safety and traceability.
- User feedback flag: correct / needs revision / unsafe / unsupported.

**Acceptance baseline**
- An AI-generated requirement can be traced to the analysis run and its sources.
- Failed evaluation cases can be stored as regression tests.

---

## 5. SHOULD — MVP if capacity permits

- Search across current project knowledge.
- Basic dashboard for open questions, risks, requirement status.
- Version comparison for requirement/decision.
- Basic Mermaid text generation for As-Is/To-Be diagrams.
- Configurable artifact templates.
- Comments on requirement during review.

These items may move to V1.1 without breaking the core architecture.

---

## 6. Out of Scope — MVP

The following must **not block MVP delivery**:

1. AI diagnosis, treatment recommendation or medication decision.
2. Patient-facing clinical chatbot.
3. Automatic approval of business/clinical/technical requirements.
4. Write/update/delete data directly in production HIS/EMR/LIS/RIS/PACS/Pharmacy systems.
5. Production patient-data ingestion as a requirement for MVP demonstration.
6. Full HL7/FHIR/DICOM interoperability engine.
7. Full hospital master data synchronization.
8. Real-time call-center/telephony integration.
9. Jira/Slack/Gmail/Teams automatic two-way sync.
10. Audio speech-to-text pipeline.
11. Advanced OCR for scanned documents.
12. Autonomous multi-agent execution.
13. Fine-tuning/custom model training.
14. Fully automated BPMN graphical editor.
15. Full test-management replacement for QC tools.
16. Legal/compliance final advice or autonomous regulatory approval.
17. Automated production release/deployment decisions.
18. Advanced analytics/BI beyond basic product/BA dashboard.

---

## 7. Core Data Objects for Development

| Object | Minimum purpose |
|---|---|
| User | Identity and role |
| Project | Workspace boundary |
| ProjectMember | Access within project |
| Source | Original knowledge source |
| Evidence | Specific support extracted from Source |
| Stakeholder | Project actor/decision authority |
| Requirement | Core analyzed requirement |
| RequirementVersion | Version/history |
| Question | Missing information |
| Assumption | Unconfirmed statement |
| Decision | Confirmed decision and supersede chain |
| Risk | Business/clinical/security/etc. risk |
| BusinessRule | Rule linked to requirement |
| AcceptanceCriteria | Validation condition |
| TraceLink | Graph relationship |
| ChangeRequest | Controlled post-baseline change |
| Review | Human review/approval record |
| Artifact | Generated output and version |
| AIAnalysisRun | Prompt/model/source/output metadata |
| AuditEvent | Important system/user/AI action log |
| GlossaryTerm | Project/domain terminology |
| RegulationReference | Regulation metadata/reference only |

---

## 8. Minimum Screens / UI Areas

1. Login.
2. Project List.
3. Project Overview.
4. Sources / Upload.
5. Source Detail + Evidence.
6. AI Analysis Workspace.
7. Questions / Decisions / Risks.
8. Requirements List.
9. Requirement Detail + History + Reviews.
10. Traceability view.
11. Change Request + Impact view.
12. Artifact generation/download area.
13. Project Glossary / Regulations.
14. Audit / AI feedback area for Admin/BA.

UI design itself is not fixed by this scope.

---

## 9. Core Service Boundaries (Technology-Neutral)

```text
Auth & Access
Project Workspace
Knowledge Ingestion
Knowledge Retrieval
AI Orchestration
BA Analysis
Requirement Management
Governance / Human Review
Traceability / Impact
Artifact Generation
Audit / Evaluation
```

Implementation may begin as a modular monolith. Microservices are **not required** by scope.

---

## 10. Critical Business / AI Rules

1. Every project object must belong to a Project ID.
2. AI retrieval must be project-scoped.
3. FACT requires evidence/source or human confirmation.
4. ASSUMPTION remains assumption until confirmed.
5. AI recommendation never becomes approved requirement automatically.
6. Conflicting active evidence generates a conflict flag.
7. Clinical-impact requirement requires Medical SME review before APPROVED/BASELINED.
8. AI cannot approve requirement.
9. Approved/baselined objects maintain version history.
10. Change after baseline goes through Change Request + Impact Analysis.
11. Artifact generation defaults to current approved/baselined data.
12. Source text cannot override system guardrails.
13. AI must expose source/evidence used for important conclusions.
14. No sensitive health data should be included in prompts/logs unless the deployment explicitly authorizes and protects it.

---

## 11. MVP Definition of Done

MVP is considered functionally complete when a BA can successfully complete this scenario without manual database manipulation:

1. Log in.
2. Create Project `PRJ-001`.
3. Define scope and stakeholders.
4. Upload/paste a meeting transcript.
5. System creates Source record.
6. AI extracts evidence and classifies facts/questions/decisions/risks.
7. BA runs requirement analysis.
8. AI identifies at least one gap/question when information is incomplete.
9. BA records an answer/decision.
10. AI creates/refines draft requirement and acceptance criteria.
11. Requirement links back to Source/Evidence.
12. BA sends requirement to Business review.
13. Clinical-impact requirement is routed to Medical SME; non-clinical requirement does not require that gate.
14. Human reviewer approves requirement.
15. System marks/version-controls the approved/baselined requirement.
16. User changes an approved requirement through a Change Request.
17. System produces linked impact items from traceability.
18. BA generates a Requirement Spec + RTM/Impact artifact.
19. Audit history shows important actions and AI generation source context.
20. A user without project permission cannot access PRJ-001 data.

---

## 12. MVP Non-Functional Baseline

Values below are **product design targets to be confirmed by Tech/Product**, not healthcare business rules.

- Security: authentication + authorization + project isolation are mandatory.
- Privacy: use de-identified/synthetic content during initial development/testing by default.
- Auditability: lifecycle/approval/change events must be recorded.
- Traceability: important AI outputs show supporting source/evidence.
- Reliability: failed AI generation must not corrupt approved/baselined objects.
- Recoverability: source and requirement records are persistent and versioned/backed up according to deployment policy.
- Explainability: system displays why an item was classified/flagged and which source was used where practical.
- Performance/SLA: exact targets are TBD and must be confirmed during Technical Design; do not hard-code arbitrary values here.

---

## 13. Development Sequence

Recommended coding order:

```text
Sprint/Phase 0
Foundation + Auth + Project + DB model

Phase 1
Source Registry + Upload + Text Extraction + Retrieval

Phase 2
AI Analysis Engine + Classification + Questions

Phase 3
Requirement/Decision/Risk Lifecycle + Human Review

Phase 4
Traceability Graph + Change/Impact

Phase 5
Artifact Generation + Dashboard

Phase 6
AI Evaluation + Audit hardening + Security hardening
```

This is a sequencing recommendation, not a fixed delivery methodology.

---

## 14. Release Gate for MVP

Do not release MVP for real healthcare project use until all MUST conditions below pass:

- [ ] Project isolation tested.
- [ ] No autonomous approval path exists.
- [ ] Clinical-impact routing to Medical SME works.
- [ ] Source/evidence is visible for approved requirement.
- [ ] Conflict case tested.
- [ ] Assumption hallucination regression test passes.
- [ ] Change Request preserves prior baseline/history.
- [ ] Audit trail exists for review/approval/change.
- [ ] Security/privacy review completed for deployment environment.
- [ ] Golden AI evaluation suite passes the agreed threshold.

---

## 15. Scope Decision

**This document is the coding-scope baseline for MVP.**  
Changes that add new MUST capabilities should be handled as a Scope Change / Change Request so the MVP does not expand uncontrollably.
