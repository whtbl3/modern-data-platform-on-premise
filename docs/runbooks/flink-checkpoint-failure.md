# Runbook: Flink Checkpoint Failing

**Alert:** `FlinkCheckpointFailing`  
**Severity:** Warning  
**Impact:** If checkpoints fail persistently, Flink cannot recover from crashes without data loss.

## Triage

```bash
# Check checkpoint status via Flink REST API
kubectl port-forward -n lakehouse-prod svc/vietmart-orders-stream-rest 8081:8081
curl http://localhost:8081/jobs/<job-id>/checkpoints | jq '.latest.failed'
```

## Common Causes

| Cause | How to Identify | Fix |
|-------|----------------|-----|
| MinIO slow/unavailable | Checkpoint timeout in logs | Check MinIO health, IO latency |
| State too large | Checkpoint size growing | Enable incremental checkpoints |
| Backpressure blocking alignment | Alignment timeout | Increase checkpoint timeout, enable unaligned checkpoints |
| TaskManager GC pressure | Long GC pauses in TM logs | Increase TM memory or reduce state |

## Resolution Steps

### Increase checkpoint timeout
```yaml
# In flink-deployment.yaml
flinkConfiguration:
  execution.checkpointing.timeout: "600000"  # 10 min (default 10 min)
  state.checkpoints.num-retained: "3"
```

### Enable incremental checkpoints (recommended for large state)
```yaml
flinkConfiguration:
  state.backend.incremental: "true"
```

### Enable unaligned checkpoints (for backpressure scenarios)
```yaml
flinkConfiguration:
  execution.checkpointing.unaligned.enabled: "true"
```

### Check MinIO write performance
```bash
kubectl exec -n lakehouse-prod minio-0 -- \
  mc admin speedtest local --duration 10s
```

## Prevention

- Monitor checkpoint duration trend in Grafana
- Set checkpoint interval = 2x expected duration
- Keep state compact: use TTL for session windows
