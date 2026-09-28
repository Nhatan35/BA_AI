# Prompt — Meeting Analyzer

Phân tích nội dung meeting dưới vai trò Medical BA.

Yêu cầu:
1. Không suy diễn ngoài hội thoại.
2. Tách riêng FACT / DECISION / REQUIREMENT / QUESTION / ASSUMPTION / RISK / ACTION ITEM.
3. Với mỗi item, chỉ ra bằng chứng/timestamp/page nếu có.
4. Phát hiện nội dung mâu thuẫn với decision/requirement cũ nếu context được cung cấp.
5. Decision mới thay thế decision cũ chỉ khi meeting thể hiện rõ việc chốt/thay đổi.
6. Liệt kê câu hỏi blocking còn thiếu.
7. Đánh dấu nội dung cần Business, Medical SME, Tech hoặc Security xác nhận.
8. Không tự tạo business rule mới.
