# Runbook: Flink Job Down

**Alert:** `FlinkJobNotRunning`  
**Severity:** Critical  
**Impact:** Real-time analytics offline. ClickHouse tables stop receiving updates.

## Triage

```bash
# Check FlinkDeployment status
kubectl get flinkdeployment -n lakehouse-prod
kubectl describe flinkdeployment vietmart-orders-stream -n lakehouse-prod

# Check JobManager logs
kubectl logs -n lakehouse-prod -l app=vietmart-orders-stream --tail=100
```

## Common Causes

| Cause | Symptoms | Fix |
|-------|----------|-----|
| OOM kill | `OOMKilled` in pod events | Increase TaskManager memory in flink-deployment.yaml |
| Savepoint corruption | `Failed to restore from savepoint` | Start from latest checkpoint or fresh |
| Kafka topic deleted/recreated | `UnknownTopicOrPartitionException` | Recreate topic, reset offsets |
| ClickHouse JDBC timeout | `Connection refused` in TM logs | Verify ClickHouse is up, check network |
| K8s node failure | Pod in Pending state | Check node status, reschedule |

## Resolution Steps

### Standard restart (from savepoint)
```bash
# Flink Operator auto-restarts from last savepoint by default
# If stuck, manually trigger:
kubectl delete pod -n lakehouse-prod -l app=vietmart-orders-stream
```

### Start fresh (discard state)
```bash
# Only if savepoint is corrupted
kubectl patch flinkdeployment vietmart-orders-stream -n lakehouse-prod \
  --type merge -p '{"spec":{"job":{"upgradeMode":"stateless"}}}'

# After job recovers, switch back to savepoint mode
kubectl patch flinkdeployment vietmart-orders-stream -n lakehouse-prod \
  --type merge -p '{"spec":{"job":{"upgradeMode":"savepoint"}}}'
```

### Increase resources
```bash
# Edit flink-deployment.yaml, increase TaskManager:
#   memory: "8g" → "12g"
#   cpu: 2 → 4
kubectl apply -f src/streaming/flink-deployment.yaml
```

## Post-recovery

After the job restarts, it will consume from the last checkpoint. Check:
1. Consumer lag is decreasing
2. ClickHouse tables have recent data: `SELECT max(window_start) FROM revenue_realtime`
3. No duplicate entries (Flink exactly-once semantics should prevent this)

## Escalation

- If job fails to restart 3 times: check K8s events for resource pressure
- If data gap > 1 hour: consider running a batch backfill for the missing period
