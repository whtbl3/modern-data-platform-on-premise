# Phase 1 — Discovery

## Những câu hỏi phải trả lời được trước khi design

### 1. Pain statement (Đau ở đâu?)
- Doanh thu chênh lệch bao nhiêu % giữa các hệ thống?
- Report mất bao lâu từ lúc request đến lúc có?
- Engineer đang mất bao nhiêu % thời gian cho ad-hoc queries?

### 2. Data sources (Có gì?)
- Bao nhiêu nguồn? Format nào (DB, file, API, CDC)?
- Volume mỗi ngày (records, GB)?
- Nguồn nào là source of truth cho revenue?

### 3. Users & Use cases (Ai dùng? Dùng để làm gì?)
- Ai xem dashboard hàng ngày? (CEO, CFO, CMO, COO, Regional Managers)
- Cần real-time hay T+1 là đủ?
- Có flash sale / spike traffic không? Peak bao nhiêu?

### 4. Constraints (Giới hạn gì?)
- On-prem hay cloud? Có bao nhiêu servers?
- Budget license: $0 (open-source only) hay có ngân sách?
- Team size: bao nhiêu người vận hành?
- Compliance: PII, data retention bao lâu?

### 5. Success criteria (Thành công = gì?)
- Revenue discrepancy giảm từ X% → Y%
- Report latency giảm từ X ngày → Y giờ
- Engineer ad-hoc time giảm từ X% → Y%

---

## Thứ tự ưu tiên khi phỏng vấn stakeholders

1. **CFO** — revenue reconciliation là critical nhất (tiền sai = vấn đề lớn)
2. **CEO** — vision, timeline, budget constraints
3. **COO** — operations pain (inventory, delivery)
4. **CMO** — customer 360, campaign ROI
5. **CTO** — technical constraints, team capacity
6. **Heads of Departments** — specific use cases

## Output của Phase 1

| Deliverable | Nội dung | Dùng để |
|-------------|----------|---------|
| Pain → Metric | "Revenue chênh 3-8%" → target "giảm còn <1%" | Đo thành công, justify project |
| Data Inventory | 6 sources, 5.8GB/day, format/frequency mỗi nguồn | Chọn stack (batch vs stream, storage size) |
| MVP Scope | Top 3-5 use cases phải có trước | Không build thừa, ship nhanh |
| Constraints | 20 servers, 5 người, $0 license | Loại trừ options không khả thi |
| Timeline | MVP 8 weeks, full 16 weeks | Set expectation với stakeholders |

## Tóm lại khi đi phỏng vấn

Hỏi 3 thứ cho mỗi stakeholder:

1. **Đang đau gì?** (problem) — "Báo cáo sai", "Mất 3 ngày mới có số"
2. **Nếu có magic, muốn gì?** (ideal outcome) — "Thấy revenue real-time khi flash sale"
3. **Chấp nhận được gì?** (constraint) — "T+1 buổi sáng là đủ", "Không cần real-time"

Câu trả lời sẽ tự phân ra:
- **Must** = nhiều người đau giống nhau → làm trước
- **Should** = 1-2 người muốn, impact cao → làm sau MVP
- **Could** = nice to have → backlog
