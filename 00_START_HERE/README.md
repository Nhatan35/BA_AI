# Medical BA AI — Starter Kit

**Baseline:** Final Conceptual Blueprint V1.0  
**Mục tiêu:** Cung cấp sườn làm việc để bắt đầu một project Business Analysis trong domain y tế và dùng AI như một BA Copilot có kiểm soát.

## Nguyên tắc bắt buộc

1. AI **không sở hữu requirement** và không tự approve.
2. AI phải phân biệt: **FACT / ASSUMPTION / QUESTION / DECISION / RECOMMENDATION / RISK / ACTION ITEM**.
3. Nội dung quan trọng phải có **Source/Evidence** hoặc được Human xác nhận.
4. Không biến Assumption thành Requirement.
5. Khi nguồn mâu thuẫn, đánh dấu **CONFLICT**; không tự chọn nguồn.
6. Requirement có tác động lâm sàng phải qua **Medical SME Review**.
7. Quyết định mới có thể **supersede** quyết định cũ; Source of Truth chỉ dùng phiên bản đang hiệu lực.
8. Mọi thay đổi sau baseline phải đi qua **Change Request + Impact Analysis**.
9. Không trộn dữ liệu giữa các project/workspace.
10. AI chỉ hỗ trợ phân tích, trace, kiểm tra, tài liệu hóa và phát hiện thiếu sót.

## Bắt đầu nhanh

1. Đọc `QUICK_START_30_MIN.md`.
2. Tạo Project ID trong `11_Master_Tracker/Medical_BA_AI_Master_Tracker.xlsx`.
3. Điền Project Charter + Scope.
4. Đăng ký tất cả nguồn trong sheet `Sources`.
5. Phân tích meeting/request bằng template ở `03_Elicitation/`.
6. Ghi Requirement/Decision/Question/Risk vào Master Tracker.
7. Chỉ tạo tài liệu chính thức từ thông tin hiện hành đã được review/approve.

## Cấu trúc thư mục

- `01_Project_Setup`: khởi tạo project, scope, stakeholder.
- `02_Knowledge_Base`: source, source of truth, glossary, regulation.
- `03_Elicitation`: intake, meeting, questions.
- `04_Analysis`: As-Is, To-Be, rule, data, permission, API, NFR, clinical risk.
- `05_Requirements`: requirement spec, user story, acceptance criteria, review.
- `06_Governance`: decision, assumption, evidence, human gate.
- `07_Traceability_Change`: traceability, impact, change request.
- `08_Test_UAT`: UAT và solution evaluation.
- `09_AI_Governance`: guardrails, evaluation, security/privacy, incidents.
- `10_Artifacts`: quy tắc sinh bộ tài liệu.
- `11_Master_Tracker`: workbook trung tâm.
- `12_AI_Prompts`: prompt mẫu để dùng với AI.
- `13_Example`: ví dụ end-to-end.

## Bắt đầu code MVP

Sau khi hiểu baseline, đọc:

1. `01_Project_Setup/Medical_BA_AI_MVP_Development_Scope_v1.0.md` — scope coding chính thức.
2. `14_Development/MVP_Epic_Backlog.md` — epic và thứ tự triển khai.
3. `14_Development/MVP_Definition_of_Done.md` — điều kiện để gọi MVP hoàn thành.

Không đưa hạng mục **Out of Scope** vào MVP nếu chưa có Scope Change.

