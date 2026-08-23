# Phase 1.2: Requirements Documentation

## Functional Requirements (FR)

| ID | Yêu cầu | Priority | Stakeholder | Acceptance Criteria |
|----|----------|----------|-------------|---------------------|
| FR-1 | Tự động ingest data từ POS (120 stores), e-commerce DB, payment gateways hàng ngày | Must | All | Data available trong raw layer < 1h sau khi source update |
| FR-2 | Unified customer view: merge online + offline customer bằng phone/email | Must | CMO, CEO | 1 customer_id duy nhất per person, match rate > 90% |
| FR-3 | Daily revenue aggregation (per store, region, channel, category) | Must | CEO, CFO, Regional Mgrs | Số liệu khớp giữa các báo cáo, sai lệch < 0.1% |
| FR-4 | Tự động reconcile revenue giữa POS, e-commerce, payment gateway | Must | CFO | Alert trong vòng 2h nếu discrepancy > 1% |
| FR-5 | Self-service SQL query cho business users | Must | CMO, COO, Regional Mgrs | Query response < 30s, không cần engineer support |
| FR-6 | Customer segmentation (RFM) tự động refresh daily | Must | CMO | Segment update mỗi sáng, phản ánh data hôm qua |
| FR-7 | Real-time dashboard khi flash sale đang chạy | Should | Head of E-commerce | Latency < 60 giây từ event → dashboard |
| FR-8 | Clickstream analysis: funnel, drop-off, session metrics | Should | Head of E-commerce | Analyze web + mobile, session stitching |
| FR-9 | Inventory monitoring: stock level per SKU per store, alert stockout | Should | COO | Alert khi stock < safety threshold |
| FR-10 | Delivery SLA tracking: % đơn giao đúng hạn per partner | Should | COO | Real-time tracking, daily report per partner |
| FR-11 | Data catalog: team mới self-onboard, tìm và hiểu data < 1 ngày | Could | CTO, Analytics team | Searchable catalog with descriptions, owners |
| FR-12 | Churn prediction: flag khách hàng có risk churn | Could | CMO | Weekly scoring, integrate với loyalty program |

---

## Non-Functional Requirements (NFR)

| ID | Yêu cầu | Target | Lý do | Measured by |
|----|----------|--------|-------|-------------|
| NFR-1 | Batch pipeline latency (end-to-end) | < 2 giờ | CEO cần data sáng hôm sau trước 8h | Pipeline completion time |
| NFR-2 | Streaming latency (event → queryable) | < 60 giây | Flash sale monitoring | Event time → ClickHouse queryable |
| NFR-3 | Query response time (ad-hoc SQL) | p95 < 30 giây | Self-service phải nhanh | Trino query duration |
| NFR-4 | Platform availability | 99.5% | Business reporting hàng ngày | Uptime monitoring |
| NFR-5 | Data freshness (batch) | T+1 trước 6:00 AM | Báo cáo sáng | Dagster sensor completion |
| NFR-6 | Data retention | 3 năm hot, 7 năm cold | Thuế + trend analysis | Storage policy |
| NFR-7 | Recovery: RPO | < 24 giờ | Không mất > 1 ngày data | Backup frequency |
| NFR-8 | Recovery: RTO | < 4 giờ | Business continuity | Disaster recovery drill |
| NFR-9 | Scalability (batch) | Handle 2x current volume | Growth projection 2 năm | Spark auto-scale |
| NFR-10 | Scalability (streaming) | Handle 10x spike (flash sale) | Black Friday, 11.11 | Flink autoscaler |
| NFR-11 | Security: PII encryption | At rest + in transit | Compliance nội bộ + PDPA | Audit report |
| NFR-12 | Security: Access control | Column-level per department | Marketing không thấy payment info | OpenMetadata policies |
| NFR-13 | Concurrent users (SQL query) | 30 users đồng thời | 3 departments + regional managers | Trino cluster capacity |

---

## Use Case Priority Matrix

```
                    HIGH BUSINESS VALUE
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         │   FR-3        │   FR-7        │
         │   FR-4        │   FR-8        │
         │   FR-1        │   FR-12       │
EASY ────┼───────────────┼───────────────┼──── HARD
         │   FR-5        │   FR-9        │
         │   FR-6        │   FR-10       │
         │   FR-11       │   FR-2        │
         │               │               │
         └───────────────┼───────────────┘
                         │
                    LOW BUSINESS VALUE
```

## MVP Scope (8 tuần)

**Must-have (Sprint 1-4)**:
- FR-1: Auto ingest (POS + e-commerce + payment)
- FR-3: Daily revenue aggregation
- FR-4: Revenue reconciliation
- FR-5: Self-service SQL
- FR-6: Customer segmentation

**Should-have (Sprint 5-8)**:
- FR-2: Unified customer view
- FR-7: Real-time flash sale dashboard
- FR-8: Clickstream analysis
- FR-9: Inventory monitoring

**Post-MVP**:
- FR-10, FR-11, FR-12
