# Example — Hủy lịch khám

Ví dụ này chỉ để minh họa cách dùng bộ khung, **không phải business rule chuẩn cho mọi bệnh viện**.

## 1. Raw request
> Lễ tân cần hủy lịch khám cho bệnh nhân.

## 2. Classification
- Domain: Appointment
- Actor: Receptionist
- Type: Functional Requirement draft

## 3. Facts
- Chưa có fact nào ngoài request.

## 4. Assumptions
- Có thể tồn tại trạng thái Appointment. → **ASSUMPTION**

## 5. Blocking questions
1. Ai được phép hủy?
2. Những trạng thái nào được hủy?
3. Lịch đã check-in có được hủy không?
4. Có bắt buộc lý do hủy không?
5. Có liên quan thanh toán/hoàn tiền không?
6. Có gửi thông báo bệnh nhân không?
7. Có cần audit ai hủy, lúc nào, lý do gì không?
8. Có downstream system nào phải đồng bộ trạng thái không?

## 6. Draft requirement — chỉ sau khi Business trả lời

`REQ-APT-001`: Hệ thống cho phép role được cấp quyền hủy appointment thỏa điều kiện business đã xác nhận.

## 7. Analysis areas
- Business Rule: trạng thái/điều kiện hủy.
- Data: cancellation_reason, cancelled_by, cancelled_at.
- Permission: role nào được hủy.
- Integration: đồng bộ với HIS/CRM/notification nếu có.
- NFR: auditability/security nếu áp dụng.
- Risk: hủy nhầm lịch đã tiếp nhận hoặc đã thu phí.

## 8. Human review
- BA: completeness.
- Business: cancellation policy.
- Medical SME: chỉ cần nếu flow có clinical impact.
- Finance: nếu có refund.
