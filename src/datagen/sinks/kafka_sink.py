"""Sink: push records as events to Kafka topics (for streaming path)."""
import json
from dataclasses import dataclass

from kafka import KafkaProducer

from .base import BaseSink


@dataclass
class KafkaConfig:
    brokers: str = "localhost:9092"
    acks: str = "all"
    batch_size: int = 16384
    linger_ms: int = 10


class KafkaSink(BaseSink):
    def __init__(self, config: KafkaConfig | None = None):
        self.config = config or KafkaConfig()
        self._producer: KafkaProducer | None = None

    def connect(self) -> None:
        self._producer = KafkaProducer(
            bootstrap_servers=self.config.brokers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks=self.config.acks,
            batch_size=self.config.batch_size,
            linger_ms=self.config.linger_ms,
        )

    def write(self, records: list[dict], target: str) -> int:
        """Write records to Kafka topic (target = topic name)."""
        if not records:
            return 0

        for record in records:
            key = record.get("order_id") or record.get("event_id") or record.get("reading_id")
            self._producer.send(topic=target, key=key, value=record)

        self._producer.flush()
        return len(records)

    def close(self) -> None:
        if self._producer:
            self._producer.close()
            self._producer = None
