# MVP Definition of Done

Một build chỉ được coi là **MVP Complete** khi đáp ứng toàn bộ nhóm sau.

## Functional
- [ ] Project workspace + role access hoạt động.
- [ ] Nạp được ít nhất text/TXT/MD/PDF text/DOCX/XLSX-CSV theo scope.
- [ ] Source + Evidence được lưu và truy xuất.
- [ ] AI phân loại FACT/ASSUMPTION/QUESTION/DECISION/RECOMMENDATION/RISK/ACTION ITEM.
- [ ] AI sinh BA gap questions.
- [ ] AI tạo draft requirement + AC.
- [ ] Requirement lifecycle và human review hoạt động.
- [ ] Clinical-impact item yêu cầu Medical SME review.
- [ ] Traceability Source → Evidence → Requirement → AC hoạt động.
- [ ] Change Request + Impact Analysis hoạt động ở mức linked-node.
- [ ] Sinh được Requirement Spec và Traceability/Impact artifact.

## Guardrails
- [ ] AI không tự approve.
- [ ] AI không tự tạo clinical policy/decision.
- [ ] Assumption không được trình bày như fact.
- [ ] Conflict không được AI tự giải quyết im lặng.
- [ ] Source content không override system instruction.
- [ ] Project A không rò sang Project B.

## Quality
- [ ] Golden evaluation cases chạy được.
- [ ] Có regression case cho hallucinated business rule.
- [ ] Có regression case cho source conflict.
- [ ] Có regression case cho clinical safety review.
- [ ] Có audit log cho create/update/review/approve/change và AI analysis metadata.

## Release readiness
- [ ] Security review hoàn thành cho môi trường deploy.
- [ ] Privacy/data handling review hoàn thành.
- [ ] Backup/recovery policy được xác định.
- [ ] Error path của AI không làm mất/corrupt baseline requirement.
