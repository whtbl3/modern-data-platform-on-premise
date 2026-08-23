"""
VietMart Data Generator — simulate all 6 source systems.

Usage:
    # Batch: load a full day of data into MinIO raw layer
    uv run python -m src.datagen --mode batch

    # Stream: continuous clickstream + order events → Kafka
    uv run python -m src.datagen --mode stream --interval 0.5

    # Flash sale simulation: 600 events/sec burst
    uv run python -m src.datagen --mode flash-sale

    # Single source only
    uv run python -m src.datagen --mode batch --source pos
"""
import argparse
import logging

from .generators import (
    ClickstreamGenerator,
    EcomCustomerGenerator,
    EcomOrderGenerator,
    GeneratorConfig,
    InventoryGenerator,
    LoyaltyMemberGenerator,
    PaymentGenerator,
    POSTransactionGenerator,
)
from .pipeline import DataGenPipeline, PipelineStep
from .sinks.kafka_sink import KafkaConfig, KafkaSink
from .sinks.minio_sink import MinIOConfig, MinIOSink

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def build_batch_pipeline(args) -> DataGenPipeline:
    """Full day batch load → MinIO raw layer (matches Data Audit volumes)."""
    config = GeneratorConfig(seed=args.seed)
    minio = MinIOConfig(
        endpoint=args.minio_endpoint,
        access_key=args.minio_access_key,
        secret_key=args.minio_secret_key,
        bucket=args.bucket,
    )

    pipeline = DataGenPipeline()
    sources = args.source.split(",") if args.source else ["all"]

    if "all" in sources or "pos" in sources:
        pipeline.add_step(PipelineStep(
            name="pos_transactions",
            generator=POSTransactionGenerator(config),
            sinks=[(MinIOSink(minio), "pos")],
            batch_size=args.pos_txns,
        ))

    if "all" in sources or "ecommerce" in sources:
        pipeline.add_step(PipelineStep(
            name="ecom_customers",
            generator=EcomCustomerGenerator(config),
            sinks=[(MinIOSink(minio), "ecommerce/customers")],
            batch_size=args.ecom_customers,
        ))
        pipeline.add_step(PipelineStep(
            name="ecom_orders",
            generator=EcomOrderGenerator(config),
            sinks=[(MinIOSink(minio), "ecommerce/orders")],
            batch_size=args.ecom_orders,
        ))

    if "all" in sources or "payments" in sources:
        pay_gen = PaymentGenerator(config)
        pipeline.add_step(PipelineStep(
            name="payments_vnpay",
            generator=pay_gen,
            sinks=[(MinIOSink(minio), "payments/vnpay")],
            batch_size=args.payments_vnpay,
        ))
        pipeline.add_step(PipelineStep(
            name="payments_momo",
            generator=pay_gen,
            sinks=[(MinIOSink(minio), "payments/momo")],
            batch_size=args.payments_momo,
        ))
        pipeline.add_step(PipelineStep(
            name="payments_card",
            generator=pay_gen,
            sinks=[(MinIOSink(minio), "payments/card")],
            batch_size=args.payments_card,
        ))

    if "all" in sources or "inventory" in sources:
        pipeline.add_step(PipelineStep(
            name="inventory",
            generator=InventoryGenerator(config),
            sinks=[(MinIOSink(minio), "inventory")],
            batch_size=args.inventory_records,
        ))

    if "all" in sources or "loyalty" in sources:
        pipeline.add_step(PipelineStep(
            name="loyalty_members",
            generator=LoyaltyMemberGenerator(config),
            sinks=[(MinIOSink(minio), "loyalty")],
            batch_size=args.loyalty_members,
        ))

    if "all" in sources or "clickstream" in sources:
        pipeline.add_step(PipelineStep(
            name="clickstream",
            generator=ClickstreamGenerator(config),
            sinks=[(MinIOSink(minio), "ecommerce/clickstream")],
            batch_size=args.clickstream_events,
        ))

    return pipeline


def build_stream_pipeline(args) -> DataGenPipeline:
    """Streaming: clickstream + order events → Kafka (real-time path)."""
    config = GeneratorConfig(seed=args.seed)
    kafka = KafkaConfig(brokers=args.kafka_brokers)

    pipeline = DataGenPipeline()

    pipeline.add_step(PipelineStep(
        name="clickstream_stream",
        generator=ClickstreamGenerator(config),
        sinks=[(KafkaSink(kafka), "clickstream")],
        batch_size=60,
    ))

    pipeline.add_step(PipelineStep(
        name="orders_stream",
        generator=EcomOrderGenerator(config),
        sinks=[(KafkaSink(kafka), "order_events")],
        batch_size=5,
    ))

    return pipeline


def run_flash_sale(args):
    """Simulate flash sale burst: 600 events/sec for 60 seconds."""
    logger.info("Starting flash sale simulation: 600 events/sec × 60s = 36,000 events")
    config = GeneratorConfig(seed=args.seed)
    kafka = KafkaConfig(brokers=args.kafka_brokers)

    gen = ClickstreamGenerator(config)
    events = gen.generate_flash_sale_burst(events_per_second=600, duration_seconds=60)

    with KafkaSink(kafka) as sink:
        written = sink.write(events, "clickstream")
        logger.info(f"Flash sale: sent {written} events to Kafka topic 'clickstream'")


def main():
    parser = argparse.ArgumentParser(description="VietMart Data Generator")
    parser.add_argument("--mode", choices=["batch", "stream", "flash-sale"], default="batch")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--source", type=str, default=None, help="Comma-separated: pos,ecommerce,payments,inventory,loyalty,clickstream")

    # Batch sizes (default = realistic daily volumes from Data Audit)
    parser.add_argument("--pos-txns", type=int, default=800000)
    parser.add_argument("--ecom-orders", type=int, default=50000)
    parser.add_argument("--ecom-customers", type=int, default=5000)
    parser.add_argument("--payments-vnpay", type=int, default=30000)
    parser.add_argument("--payments-momo", type=int, default=15000)
    parser.add_argument("--payments-card", type=int, default=20000)
    parser.add_argument("--inventory-records", type=int, default=100000)
    parser.add_argument("--loyalty-members", type=int, default=10000)
    parser.add_argument("--clickstream-events", type=int, default=500000)

    # Stream config
    parser.add_argument("--interval", type=float, default=1.0)

    # Sink configs
    parser.add_argument("--minio-endpoint", default="http://localhost:9000")
    parser.add_argument("--minio-access-key", default="minioadmin")
    parser.add_argument("--minio-secret-key", default="minioadmin")
    parser.add_argument("--bucket", default="dev-raw")
    parser.add_argument("--kafka-brokers", default="localhost:9092")

    args = parser.parse_args()

    if args.mode == "batch":
        pipeline = build_batch_pipeline(args)
        pipeline.run_batch()
    elif args.mode == "stream":
        pipeline = build_stream_pipeline(args)
        pipeline.run_stream(interval_seconds=args.interval)
    elif args.mode == "flash-sale":
        run_flash_sale(args)


if __name__ == "__main__":
    main()
