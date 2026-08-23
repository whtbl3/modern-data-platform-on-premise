# Runbook: dbt Test Failure

**Alert:** `DbtTestFailure`  
**Severity:** Critical  
**Impact:** Data quality issue detected. Marts may contain incorrect data.

## Triage

```bash
# Run dbt test locally to see which tests failed
cd src/transforms
uv run dbt test --target prod 2>&1 | grep FAIL

# Get detailed failure info
uv run dbt test --target prod --store-failures
```

## Common Failures by Model

### fct_reconciliation — discrepancy > threshold
**Meaning:** Revenue mismatch between POS, e-commerce, and payment gateways.

```sql
-- Check which stores/dates have discrepancy
SELECT * FROM analytics.fct_reconciliation
WHERE alert_level IN ('WARNING', 'CRITICAL')
ORDER BY discrepancy_pct DESC
LIMIT 20;
```

**Likely causes:**
- POS data arrived late (check raw_pos_transactions freshness)
- Payment gateway API returned partial data
- Duplicate transactions in one source

### dim_customers — duplicate customer_uid
**Meaning:** Identity resolution produced duplicates.

```sql
SELECT customer_uid, COUNT(*) FROM analytics.dim_customers
GROUP BY customer_uid HAVING COUNT(*) > 1;
```

**Fix:** Check `int_customers_unified` join logic. Phone normalization may have edge cases.

### stg_payments__consolidated — invalid status
**Meaning:** Unknown payment status from gateway.

```sql
SELECT DISTINCT status FROM staging.stg_payments__consolidated
WHERE status NOT IN ('success', 'failed', 'pending', 'refunded');
```

**Fix:** Add new status to `stg_payments__consolidated.sql` mapping.

### fct_inventory_alerts — missing store_id
**Meaning:** SAP export included unknown store codes.

**Fix:** Check if new stores were added. Update `seeds/seed_stores.csv`.

## Resolution Steps

```bash
# 1. Fix the model or seed data
# 2. Re-run only the affected models
cd src/transforms
uv run dbt run --select <failed_model>+
uv run dbt test --select <failed_model>+

# 3. If test was wrong (false positive), update the test threshold
# Edit: models/marts/<domain>/_schema.yml
```

## Escalation

- If `fct_reconciliation` CRITICAL: notify Finance team immediately
- If `dim_customers` duplicates: Marketing campaigns may double-target customers
- If tests pass on re-run without code changes: likely a transient source data issue — add data quality alert
