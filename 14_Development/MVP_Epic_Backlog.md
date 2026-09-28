# MVP Epic Backlog

| Epic | Tên | Priority | Outcome |
|---|---|---|---|
| EPIC-01 | Authentication & Workspace Isolation | MUST | User/project được phân quyền và tách dữ liệu |
| EPIC-02 | Project Setup & Context | MUST | AI biết context/scope/stakeholder của project |
| EPIC-03 | Knowledge Ingestion & Source Registry | MUST | Nạp và quản lý nguồn có metadata |
| EPIC-04 | Evidence & Source of Truth | MUST | AI output có căn cứ; conflict được flag |
| EPIC-05 | Medical BA Analysis Engine | MUST | Request → analysis/gaps/draft requirement |
| EPIC-06 | Questions / Decisions / Assumptions / Risks | MUST | Quản trị các record BA cốt lõi |
| EPIC-07 | Requirement Lifecycle & Human Review | MUST | Draft → review → approve/baseline có kiểm soát |
| EPIC-08 | Traceability & Requirement Graph | MUST | Source/Evidence/Requirement/AC được nối với nhau |
| EPIC-09 | Change & Impact Analysis | MUST | Thay đổi được kiểm soát và tìm impact |
| EPIC-10 | Artifact Generation | MUST | Sinh output BA có thể dùng/chia sẻ |
| EPIC-11 | AI Guardrails / Audit / Evaluation | MUST | AI có kiểm soát, audit và regression evaluation |
| EPIC-12 | Search / Dashboard / Diagram Helpers | SHOULD | Tăng usability, không block core MVP |

## Recommended implementation slices

### Slice A — Foundation
EPIC-01 + EPIC-02 + data model foundation.

### Slice B — Knowledge
EPIC-03 + EPIC-04.

### Slice C — Core AI BA
EPIC-05 + EPIC-06.

### Slice D — Governance
EPIC-07.

### Slice E — Change-aware BA
EPIC-08 + EPIC-09.

### Slice F — Usable outputs
EPIC-10.

### Slice G — Hardening
EPIC-11 + selected EPIC-12.
