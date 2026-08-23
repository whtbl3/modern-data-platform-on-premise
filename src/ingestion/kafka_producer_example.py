"""
Example Kafka producer for testing streaming pipeline.
Generates fake order events into Kafka topic.
"""
import json
import os
import random
import time
from datetime import UTC, datetime

from kafka import KafkaProducer


def create_order_event():
    return {
        "order_id": f"ord_{random.randint(100000, 999999)}",
        "customer_id": f"cust_{random.randint(1, 1000)}",
        "amount": round(random.uniform(10.0, 500.0), 2),
        "status": random.choice(["pending", "completed", "cancelled"]),
        "event_time": datetime.now(UTC).isoformat(),
    }


def main():
    brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "orders")

    producer = KafkaProducer(
        bootstrap_servers=brokers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"Producing to {topic} on {brokers}")

    while True:
        event = create_order_event()
        producer.send(topic, value=event)
        print(f"Sent: {event['order_id']} amount={event['amount']}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
