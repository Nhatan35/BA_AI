# Requirement Traceability Matrix — Guide

Trace các mối quan hệ:

```text
SOURCE → EVIDENCE → BUSINESS NEED → DECISION → REQUIREMENT
→ BUSINESS RULE / DATA / ROLE / API / NFR
→ USER STORY → AC → TEST/UAT
```

Mỗi relation được ghi trong sheet `Traceability`:
- From Type
- From ID
- Relation
- To Type
- To ID
- Status

Nếu node bị supersede, kiểm tra toàn bộ downstream relation.
