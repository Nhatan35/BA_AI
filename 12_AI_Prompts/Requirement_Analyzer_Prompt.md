# Prompt — Requirement Analyzer

Phân tích request sau theo Medical BA Blueprint.

Output:
- Business Need
- Actors/Stakeholders
- Requirement classification
- Facts / Decisions / Assumptions
- Missing information
- Blocking questions
- As-Is nếu đủ dữ liệu
- To-Be draft nếu được yêu cầu
- Business Rules
- Data
- Role/Permission
- Integration/API
- Exceptions
- NFR
- Risks/Clinical Safety
- Privacy/Security/Regulatory flags
- Draft Requirement + Acceptance Criteria
- Source/Evidence
- Required human reviews

Guardrail: không tự tạo policy, SLA, threshold hoặc clinical decision chưa được nguồn xác nhận.
