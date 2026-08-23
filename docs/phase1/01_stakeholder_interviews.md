# Phase 1.1: Stakeholder Interviews

## Tổng quan các bên liên quan

| Stakeholder | Vai trò | Phòng ban | Quan tâm chính |
|-------------|---------|-----------|----------------|
| CEO | Ra quyết định chiến lược | Board | Revenue overview, growth |
| CFO | Quản lý tài chính | Finance | P&L accuracy, cost control |
| CMO | Marketing & loyalty | Marketing | Customer segmentation, campaign ROI |
| COO | Vận hành chuỗi | Operations | Inventory, fulfillment, SLA |
| CTO | Hạ tầng công nghệ | IT/Engineering | Platform stability, team productivity |
| Head of E-commerce | Kênh online | Digital | Conversion, traffic, real-time |
| Store Regional Managers (3) | Quản lý khu vực | Retail | Daily performance per store |

---

## Chi tiết phỏng vấn

### CEO — Ông Minh Trần
**Câu hỏi**: "Ông cần xem data gì, khi nào, format nào?"

**Trả lời**:
> - Mỗi sáng 8h tôi cần biết: doanh thu hôm qua (online + offline), so với cùng kỳ
> - Hàng tuần: top/bottom 10 cửa hàng, sản phẩm trending up/down
> - Hàng tháng: P&L consolidated, không muốn chờ Finance merge Excel 5 ngày

**Pain points**:
- Doanh thu báo cáo khác nhau giữa Finance, Operations, E-commerce (sai số 3-8%)
- Ra quyết định mở/đóng cửa hàng dựa trên "cảm tính" vì data chậm 1 tuần
- Không biết khách hàng offline và online có overlap bao nhiêu

---

### CFO — Bà Lan Nguyễn
**Câu hỏi**: "Revenue reconciliation hiện tại diễn ra thế nào?"

**Trả lời**:
> - Cuối tháng Finance phải merge 3 nguồn: POS (120 files CSV), e-commerce DB export, payment gateway report
> - Mất 3-5 ngày, 2 người làm full-time, sai số 5% do format date khác nhau
> - Muốn daily reconciliation tự động, alert nếu sai lệch > 1%

**Pain points**:
- 120 cửa hàng x 30 ngày = 3,600 file CSV/tháng, merge bằng tay
- Payment gateway (VNPay, Momo, card) mỗi cái format khác
- Không phát hiện được fraud/discrepancy kịp thời

---

### CMO — Anh Đức Phạm
**Câu hỏi**: "Làm sao biết campaign nào hiệu quả? Khách hàng segment thế nào?"

**Trả lời**:
> - Hiện tại chạy campaign → 2 tuần sau mới biết kết quả (nhờ engineer query)
> - Không biết khách online có mua offline không (unified customer view)
> - Loyalty program có 1.5M members nhưng không biết ai sắp churn

**Pain points**:
- Yêu cầu engineer query ad-hoc → mất 3-5 ngày (backlog)
- Không có real-time view khi campaign đang chạy (flash sale 2h mà 2 tuần sau mới biết)
- RFM segmentation làm 1 lần trên Excel, 6 tháng mới refresh

---

### COO — Anh Hùng Lê
**Câu hỏi**: "Phát hiện vấn đề inventory và fulfillment thế nào?"

**Trả lời**:
> - Mỗi khu vực có Excel inventory riêng, cuối tuần mới consolidate
> - Out-of-stock phát hiện khi khách complain, không proactive
> - Delivery SLA (24h nội thành) chỉ đo được cuối tháng, không real-time
> - 3 warehouse không biết nên chuyển hàng cho nhau khi nào

**Pain points**:
- Stockout trung bình 3 ngày trước khi phát hiện → mất revenue
- Warehouse transfer decision dựa vào kinh nghiệm, không data
- Delivery partner performance (Grab, Ahamove, nội bộ) không so sánh được

---

### CTO — Anh Nam Vũ
**Câu hỏi**: "Team data hiện tại làm gì? Bottleneck ở đâu?"

**Trả lời**:
> - 3 data engineers, 70% thời gian làm ad-hoc queries cho business
> - ETL pipeline hiện tại: cron job + bash script + PostgreSQL → fragile
> - Mỗi lần POS thay đổi format → pipeline break → 2 ngày fix
> - Muốn: self-service cho business, engineers tập trung build platform

**Pain points**:
- 3 engineers nhưng 0 time cho platform work vì ad-hoc chiếm hết
- Pipeline không có monitoring, fail silently → data stale mà không ai biết
- On-premise servers dùng 30% capacity, phần còn lại idle

---

### Head of E-commerce — Chị Thảo Mai
**Câu hỏi**: "Online platform cần gì từ data?"

**Trả lời**:
> - Real-time: khi flash sale đang chạy, cần biết conversion rate, cart abandonment ngay
> - Clickstream analysis: user journey, where they drop off
> - Recommendation engine: "mua cùng với", "có thể bạn thích" → hiện tại hardcode

**Pain points**:
- Flash sale 2h nhưng chỉ biết kết quả 2 tuần sau
- Website 5M pageviews/ngày nhưng chưa phân tích gì
- Mobile app events gửi về nhưng không ai xử lý (lưu file rồi để đó)

---

### Regional Manager Miền Nam — Anh Bình Đặng
**Câu hỏi**: "Quản lý 45 cửa hàng, cần data gì hàng ngày?"

**Trả lời**:
> - Mỗi sáng cần: revenue hôm qua per store, so với target
> - Hàng tuần: staff productivity (revenue per employee), top/bottom stores
> - Muốn tự xem, không phải gọi HQ xin report

**Pain points**:
- HQ gửi report cuối tuần, đã muộn để action
- Không so sánh được stores cùng khu vực (thiếu benchmark)
- Khi weather event (mưa lớn, lễ hội) không biết impact real-time
