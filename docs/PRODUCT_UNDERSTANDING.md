# Product understanding — Phase 0

Phase 0 product assessment, 2026-09-28, accepted by the user's subsequent Phase 1 request. Phase 1 implements the foundation described in [its result](PHASE_1_RESULT.md); later product capabilities below remain the baseline objective. DEC-MVP-001–007 are recorded in the [assessment](BASELINE_ASSESSMENT.md).

## Authority and inspected material

The product source of truth is the supplied kit, especially the [development scope](../01_Project_Setup/Medical_BA_AI_MVP_Development_Scope_v1.0.md), [epic backlog](../14_Development/MVP_Epic_Backlog.md), and [definition of done](../14_Development/MVP_Definition_of_Done.md). The user's explicit instructions control this turn's phase boundary and default stack. Templates and sample rows illustrate structure; they do not approve healthcare rules.

All 53 original files were inspected: 50 Markdown files, one YAML configuration template, the manifest, and one XLSX workbook. This includes every numbered directory from `00_START_HERE` through `14_Development`, all five AI prompts, and the appointment-cancellation example. All workbook populated cells, formulas, and validation lists were read from its Open XML parts; Excel was not used to recalculate or render it. See [baseline assessment](BASELINE_ASSESSMENT.md) and the reproducible [inspection snapshot](baseline-inspection.json).

The workspace initially has no application, dependency manifests, migrations, tests, or Git metadata. No applicable AGENTS.md was found in the workspace or its ancestor directories. Node/npm and Git commands are available; the `python` command fails to start, and `py` and `docker` are not on PATH. These observations are not an exhaustive inventory of installed software. Phase 1 must establish working runtimes before claiming a runnable application.

## Product and ownership

Medical BA AI is a healthcare Business Analyst workspace. A BA turns project requests and documents into structured, evidence-grounded, reviewable requirements. It does not deliver patient diagnosis, treatment, medication decisions, or final legal/compliance conclusions.

The flow is project context → ingestion → source registry → evidence → BA analysis → gaps/questions/assumptions/risks → draft requirements/rules/AC → human review → approval/baseline → traceability → change request/impact → versioned artifacts. UAT drafts and solution feedback support the BA loop; this is not a full QC management system.

| Actor | Baseline responsibility |
|---|---|
| BA | Elicitation, analysis quality, provenance, traceability, draft authoring |
| Business Owner / Product Owner | Business decisions and approval; priority where applicable |
| Medical SME | Clinical review and clinical decisions |
| Tech Lead / Architect | Assigned technical/integration/NFR review |
| Security / Compliance | Assigned security/privacy/regulatory review |
| QC / Viewer | Read requirements/AC and use UAT output |
| Admin | Identity, membership, basic administration |
| AI | Analyze, classify, detect gaps/conflicts, propose drafts; never approve |

Stakeholders may describe external people who do not have a login. Being named as a stakeholder or business owner does not grant application permissions. The healthcare roles described in a project's permission matrix (for example Doctor) are not this application's RBAC roles.

## Scope preserved

EPIC-01 through EPIC-11 are MUST. Required inputs are pasted text, TXT, Markdown, text PDF, DOCX, CSV, XLSX. Required outputs include on-screen structured data, Markdown/text, and XLSX tabular exports. DOCX export is SHOULD; accepting DOCX input is MUST. EPIC-12 search UI/dashboard/diagram helpers remains secondary. Retrieval needed by AI is mandatory even if a standalone search page is deferred.

No production HIS/EMR/LIS/RIS/PACS/Pharmacy writes; no live enterprise synchronization, full interoperability engine, production patient-data requirement, advanced OCR/transcription, autonomous agents, fine-tuning, graphical BPMN editor, or automated release decisions. The twenty-item artifact index describes possible packages; it does not require every artifact for every project.

## Meaning of the core records

- Project is the access boundary. Membership controls people; it is separate from business stakeholders.
- Source is an original document/meeting/file; SourceVersion preserves its bytes and parser result. Evidence cites an exact location in a specific version. A source can be ACTIVE without its statements being approved business truth.
- Requirement is a stable identity; RequirementVersion holds reviewed content. BusinessRule and AcceptanceCriteria are distinct, linked records. DataDictionary, RolePermission, Integration and NFR capture analyzed specifications, not live hospital records or executable interfaces.
- Question captures a gap and an attributed answer. Assumption stays unconfirmed until a recorded human confirmation. Decision records authority and an explicit supersede chain. Risk records possible harm and mitigation.
- Traceability links provenance, requirements, rules, data, permissions, integration, AC, UAT, changes and artifacts in both directions. ChangeRequest controls post-baseline modifications; ImpactItems preserve proposed and human-confirmed effects.
- Glossary and RegulationReference preserve project definitions and referenced regulatory material. They are not autonomous legal interpretations.
- AIAnalysisRun and AIOutputItem preserve structured proposals and citations. Review, HumanConfirmation and AuditLog provide human authority and history. AIEvaluationCase/Run/Result and AIIncident support repeatable quality checks and regressions.

## Non-negotiable invariants and planned enforcement

| Rule | Enforcement design | Verification phase |
|---|---|---|
| Every project object belongs to one project | Required project IDs, composite FKs, authorized context, RLS, scoped files/jobs/cache | 1 onward |
| No source and no human confirmation means no FACT | Citation ownership/existence checks; provenance gate; unresolved support becomes a question/assumption | 2, 4, 5 |
| Seven information classes stay distinct | Validated classification enum separate from domain record type | 3, 4 |
| AI cannot approve | No AI permission to use approval commands; human identity captured server-side | 1, 4, 5 |
| Clinical impact needs Medical SME review | Version-bound required gate; conservative flags; backend approval/baseline precondition | 4, 5 |
| No invented thresholds | Explicit support for policy/number claims; unknowns remain TBD/blocking questions; golden tests | 4, 9 |
| Supersession is explicit | Authorized replacement relationship, atomic activation, preserved old records | 3, 5 |
| Baselines are protected | Immutable snapshots, CR + confirmed impact, new version and fresh review | 5, 7 |
| Conflicts are visible | Conflict record and resolution authority; recency alone cannot choose a winner | 2, 4, 5 |
| Artifacts use current approved content | Version-pinned input manifest; separate visibly labeled drafts | 8 |

## First end-to-end acceptance scenario

Use synthetic project information and the user request: “Phòng khám muốn cho phép bệnh nhân hủy lịch khám.” Preserve that raw text as source evidence. The starter example instead says the receptionist cancels for a patient; this difference is a question about actors, not permission to assume patient self-service.

1. Log in, create a project, record scope/stakeholders, ingest the request and inspect its source/evidence.
2. Run structured analysis. Ask who can cancel, allowed statuses, checked-in handling, required reason, payment/refund, notification, queue/resources, downstream synchronization, and audit. Do not invent a cancellation window.
3. BA records attributed answers/decisions; authorized humans confirm policy. A new analysis run references those answers and preserves the previous run.
4. Produce supported draft requirements/rules/AC. BA reviews, Business approves, and Medical SME reviews if clinical impact exists. Baseline the reviewed version.
5. Trace from evidence to requirement, rule, AC, UAT draft and generated artifact.
6. Record “Checked-in appointments can no longer be cancelled” as a new source/change request. Analyze linked requirements/rules/UAT/artifacts; flag missing links. Humans confirm impact and approve the CR.
7. Create a new draft version with the approved CR reference, review it, and generate an updated draft artifact. The previous baseline and artifact remain inspectable; current official output changes only after the replacement is approved/baselined.
8. Confirm that an unauthorized user and another project cannot retrieve any of these records, files or AI outputs.

This is a future executable acceptance scenario, not a completed demonstration. Detailed phases, tests, unresolved assumptions and release gates are in the [implementation plan](IMPLEMENTATION_PLAN.md).
