# Runbook: Spark Executor OOM

**Alert:** `SparkExecutorOOM`  
**Severity:** Warning  
**Impact:** Batch job may fail or retry. Data freshness delayed.

## Triage

```bash
# Find the failed Spark application
kubectl get pods -n lakehouse-prod -l spark-role=executor --field-selector status.phase=Failed

# Check executor logs for OOM
kubectl logs -n lakehouse-prod <executor-pod> --previous | grep -i "OutOfMemory\|killed"

# Check Dagster for which asset triggered the Spark job
# Dagster UI → Runs → find the failed run with Spark error
```

## Common Causes

| Scenario | Root Cause | Fix |
|----------|-----------|-----|
| POS ingestion OOM | 800K records with many items per transaction | Increase partition count or executor memory |
| Staging dedup OOM | Large shuffle during `dropDuplicates` | Increase `spark.sql.shuffle.partitions` |
| Join explosion | Intermediate model with bad join key | Fix join condition in dbt model |
| Skewed partition | One store has 10x more data | Add salting or use adaptive query execution |

## Resolution Steps

### Increase executor memory (quick fix)

Edit `infra/helm/spark/values-prod.yaml`:
```yaml
executor:
  memory: "8g"  # was 4g
  memoryOverhead: "2g"
```

Or for a specific job, set in `dagster_project/resources/__init__.py`:
```python
.config("spark.executor.memory", "8g")
.config("spark.executor.memoryOverhead", "2g")
```

### Increase partitions (for shuffle-heavy jobs)

```python
.config("spark.sql.shuffle.partitions", "400")  # default is 200
.config("spark.sql.adaptive.enabled", "true")
.config("spark.sql.adaptive.coalescePartitions.enabled", "true")
```

### Handle data skew

```python
.config("spark.sql.adaptive.skewJoin.enabled", "true")
.config("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")
```

## Prevention

- Monitor executor memory usage in Spark UI: `http://spark-master:8080`
- Set memory alerts at 80% of allocation
- KEDA scales executors horizontally, but individual executor memory is fixed — plan for largest partition
- For POS data: partition by `store_id` (120 partitions) instead of date (1 partition)
