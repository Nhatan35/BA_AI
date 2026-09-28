# Medical BA AI — Final Conceptual Blueprint V1.0

## Core flow

```text
PROJECT WORKSPACE
  ↓
KNOWLEDGE INGESTION
  ↓
BA BRAIN + MEDICAL BRAIN + PROJECT BRAIN
  ↓
REGULATION + GLOSSARY + SOURCE OF TRUTH
  ↓
EVIDENCE / PROVENANCE
  ↓
BA ORCHESTRATOR
  ↓
ELICITATION + ANALYSIS + REVIEW
  ↓
REQUIREMENT ENGINE
  ↓
DECISION MANAGEMENT + RISK MANAGEMENT
  ↓
REQUIREMENT LIFECYCLE
  ↓
REQUIREMENT GRAPH
  ↓
TRACEABILITY + IMPACT ANALYSIS
  ↓
HUMAN REVIEW
  ↓
APPROVE / BASELINE
  ↓
DEV + QC + ARTIFACT ENGINE
  ↓
UAT → RELEASE → SOLUTION EVALUATION
  ↓
FEEDBACK → CHANGE REQUEST ↺
```

## 4 lớp kiểm soát xuyên suốt

- AI Security & Access Control
- Health Data Governance & Privacy
- AI Quality / Evaluation / Audit
- AI Operations / Monitoring

## Ownership

- Business: quyết định nghiệp vụ.
- Medical SME: quyết định lâm sàng.
- BA: chất lượng phân tích và traceability.
- Product Owner: priority khi áp dụng.
- Architect/Tech Lead: technical architecture.
- Security/Compliance: phê duyệt phạm vi tương ứng.
- QC: chất lượng detailed testing.
- AI: hỗ trợ phân tích, phát hiện, trace, sinh tài liệu; không tự approve.
