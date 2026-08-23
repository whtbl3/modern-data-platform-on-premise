# Phase 1.3: Data Audit — Kiểm kê dữ liệu hiện tại

## Data Source Inventory

| Source | System | Format | Volume | Frequency | Owner | Quality Issues |
|--------|--------|--------|--------|-----------|-------|----------------|
| POS Transactions | Oracle POS (120 stores) | CSV export | 800K txn/ngày | Every 15 min (batch) | Operations | 1.5% duplicates (network retry), date format inconsistent giữa stores |
| E-commerce Orders | PostgreSQL (internal) | DB tables | 50K orders/ngày | Real-time (CDC capable) | Engineering | Clean, well-structured |
| E-commerce Clickstream | Custom event tracker | JSON events | 5M events/ngày (~60 events/sec) | Real-time stream | Engineering | 3% malformed JSON (old mobile SDK) |
| Payment Gateway — VNPay | SFTP file drop | CSV | 30K txn/ngày | Hourly batch | Finance | Amount in VND (integer), transaction_id format varies |
| Payment Gateway — Momo | API webhook | JSON | 15K txn/ngày | Real-time | Finance | Occasional duplicates on retry |
| Payment Gateway — Card (bank) | SFTP file drop | CSV | 20K txn/ngày | Daily 2:00 AM | Finance | Date format DD/MM/YYYY, amount includes fee |
| Loyalty Program | MySQL | DB tables | 1.5M members | Real-time (CDC) | Marketing | Phone number format inconsistent (+84 vs 0xx) |
| Inventory System | SAP (on-prem) | IDoc/CSV export | 50K SKUs x 120 stores | Every 30 min | Operations | Delayed sync, sometimes 2h behind reality |
| Delivery Partners | 3 APIs (Grab, Ahamove, internal) | REST JSON | 20K shipments/ngày | Real-time API pull | Operations | Each partner different schema, status codes |
| HR/Staff | HRIS system | CSV export | 8K employees | Weekly | HR | Not critical for data platform MVP |

---

## Volume Analysis

### Daily totals
```
POS Transactions:        800,000 records/day × ~500 bytes = ~400 MB/day
E-commerce Orders:        50,000 records/day × ~2 KB     = ~100 MB/day
Clickstream Events:    5,000,000 events/day  × ~800 bytes = ~4 GB/day
Payment (all gateways):   65,000 records/day × ~300 bytes = ~20 MB/day
Inventory Snapshots:   6,000,000 records/day × ~200 bytes = ~1.2 GB/day (50K SKU × 120 stores)
Delivery Tracking:        20,000 records/day × ~1 KB      = ~20 MB/day
Loyalty Events:          100,000 events/day  × ~500 bytes = ~50 MB/day

TOTAL RAW INGESTION: ~5.8 GB/day → ~175 GB/month → ~2.1 TB/year
```

### Peak loads
- Flash sale (11.11, Black Friday): clickstream 10x normal = 600 events/sec
- Tết holiday: POS 3x normal = 2.4M txn/day
- End of month: reconciliation queries heavy (Finance)

---

## Data Quality Issues Discovered

### 1. POS System (Critical)
```
Issue                    Impact              Frequency
─────                    ──────              ─────────
Duplicate transactions   Revenue inflate     1.5% of records
Date format varies       Parse failures      Stores use DD/MM, MM/DD, ISO mixed
Missing store_id         Cannot attribute    0.2% of records
Negative amounts         Refund mixed in     Valid but needs separate handling
Network timeout retry    Same txn sent 2x    During peak hours
```

### 2. E-commerce Clickstream (Medium)
```
Issue                    Impact              Frequency
─────                    ──────              ─────────
Malformed JSON           Events dropped      3% (old mobile SDK v2.x)
Missing session_id       Cannot stitch       1% (cookie blocked)
Bot traffic              Inflate metrics     ~15% of events
Timezone inconsistent    Event ordering      Mobile app sends local time
```

### 3. Payment Gateways (High)
```
Issue                    Impact              Frequency
─────                    ──────              ─────────
Amount format differs    VNPay: integer(VND)  100% need normalization
                         Momo: decimal(VND)
                         Card: includes fee
Transaction ID format   Cannot cross-ref     Each gateway different prefix
Duplicate webhooks      Double-count          2% on Momo
Settlement vs capture   Timing mismatch      Daily (card settles T+1)
```

### 4. Cross-system
```
Issue                    Impact              Frequency
─────                    ──────              ─────────
Customer identity       Cannot unify         phone: +84 vs 0xx vs spaces
                                             email: case-sensitive in some systems
No global order_id      POS order ≠          Cannot link POS → payment → delivery
                        payment txn_id
Timezone               Stores in UTC+7       Some systems log UTC, some local
                       but servers in UTC
```

---

## Current Data Flow (AS-IS)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CURRENT STATE (Fragmented, Manual, Slow)                                 │
│                                                                          │
│  POS (120 stores) ──CSV──> Shared drive ──> Finance team (Excel merge)  │
│                                                                          │
│  E-commerce DB ──> pg_dump ──> cron job ──> PostgreSQL (analytics)       │
│                                              ↓                           │
│                                        Ad-hoc queries by engineers       │
│                                                                          │
│  Payment (SFTP) ──> Manual download ──> Finance team (Excel reconcile)  │
│                                                                          │
│  Clickstream ──> Log files ──> Nobody processes (stored, unused)         │
│                                                                          │
│  Inventory (SAP) ──> Email report ──> Operations (manual monitoring)    │
│                                                                          │
│  RESULT: 5+ days to get consolidated report                             │
│          3-8% discrepancy between departments                            │
│          Engineers spend 70% time on ad-hoc queries                      │
│          Real-time data: NONE                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Metrics to Track

| Metric | Current | Target | Measured by |
|--------|---------|--------|-------------|
| Time to daily report | 3-5 days | < 2 hours (T+1 6AM) | Pipeline completion |
| Revenue discrepancy | 3-8% | < 0.1% | Reconciliation job |
| Ad-hoc query turnaround | 3-5 days | < 30 seconds (self-service) | Trino query time |
| Engineer time on ad-hoc | 70% | < 10% | Sprint tracking |
| Data staleness | 1 week | < 1 day (batch), < 1 min (stream) | Freshness monitor |
| Clickstream utilization | 0% (stored unused) | 100% analyzed | Pipeline coverage |
