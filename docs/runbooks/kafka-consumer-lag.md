# Runbook: Kafka Consumer Lag

**Alert:** `KafkaConsumerLag` / `KafkaConsumerLagCritical`  
**Severity:** Warning / Critical  
**Impact:** Real-time dashboards (revenue, flash sale, sessions) show stale data.

## Triage

```bash
# Check current lag
kubectl exec -n lakehouse-prod kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group flink-orders-consumer

kubectl exec -n lakehouse-prod kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group flink-clickstream-consumer
```

## Common Causes

| Cause | How to Identify | Fix |
|-------|----------------|-----|
| Flink job crashed | `kubectl get flinkdeployment -n lakehouse-prod` shows error | Restart Flink job |
| Traffic spike (flash sale) | Lag on `clickstream` only, during known sale | Wait for autoscaler, or manually scale |
| ClickHouse slow inserts | Flink backpressure > 0.8 | Check ClickHouse, optimize table, add replicas |
| Kafka broker overloaded | Lag on all topics | Check Cruise Control, rebalance partitions |

## Resolution Steps

### Flink job is down
```bash
# Check status
kubectl get flinkdeployment -n lakehouse-prod

# Restart with savepoint
kubectl delete flinkdeployment vietmart-orders-stream -n lakehouse-prod
kubectl apply -f src/streaming/flink-deployment.yaml
```

### Scale Flink manually (if autoscaler is too slow)
```bash
kubectl patch flinkdeployment vietmart-clickstream-stream -n lakehouse-prod \
  --type merge -p '{"spec":{"job":{"parallelism": 12}}}'
```

### Reset consumer offset (data loss — last resort)
```bash
kubectl exec -n lakehouse-prod kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group flink-orders-consumer \
  --topic order_events \
  --reset-offsets --to-latest --execute
```

## Escalation

- Warning (>100K): monitor for 15 min, check if autoscaler is catching up
- Critical (>500K): page on-call, manual scale immediately
- If lag persists 30+ min after scaling: investigate ClickHouse insert throughput
