"""
DataGen Pipeline — orchestrates generators and sinks.

Usage:
    uv run python -m src.datagen.pipeline --mode batch
    uv run python -m src.datagen.pipeline --mode stream --interval 1.0
"""
import logging
import time
from dataclasses import dataclass, field

from .generators.base import BaseGenerator
from .sinks.base import BaseSink

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class PipelineStep:
    """Connects one generator to one or more sinks."""
    name: str
    generator: BaseGenerator
    sinks: list[tuple[BaseSink, str]]  # (sink, target_name)
    batch_size: int = 1000


@dataclass
class DataGenPipeline:
    """Orchestrates multiple pipeline steps."""
    steps: list[PipelineStep] = field(default_factory=list)

    def add_step(self, step: PipelineStep):
        self.steps.append(step)

    def run_batch(self):
        """Run all steps once in batch mode."""
        logger.info("Starting batch generation...")
        total = 0

        for step in self.steps:
            records = step.generator.generate_batch(step.batch_size)
            logger.info(f"[{step.name}] Generated {len(records)} records")

            for sink, target in step.sinks:
                with sink:
                    written = sink.write(records, target)
                    logger.info(f"[{step.name}] Wrote {written} records → {target}")
                    total += written

        logger.info(f"Batch complete. Total records written: {total}")
        return total

    def run_stream(self, interval_seconds: float = 1.0, batch_size: int = 10):
        """Run continuously, generating small batches at intervals."""
        logger.info(f"Starting stream mode (interval={interval_seconds}s, batch={batch_size})")

        sinks_connected = []
        for step in self.steps:
            for sink, _ in step.sinks:
                sink.connect()
                sinks_connected.append(sink)

        try:
            while True:
                for step in self.steps:
                    records = step.generator.generate_batch(batch_size)
                    for sink, target in step.sinks:
                        sink.write(records, target)
                    logger.info(f"[{step.name}] Streamed {len(records)} → targets")

                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Stream stopped by user.")
        finally:
            for sink in sinks_connected:
                sink.close()
