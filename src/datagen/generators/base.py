"""Base class for all VietMart data generators."""
import random
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass
class GeneratorConfig:
    batch_size: int = 1000
    seed: int | None = None
    num_stores: int = 120
    num_customers: int = 50000
    num_products: int = 5000


class BaseGenerator(ABC):
    def __init__(self, config: GeneratorConfig | None = None):
        self.config = config or GeneratorConfig()
        self._rng = random.Random(self.config.seed)

    @abstractmethod
    def generate_one(self) -> dict:
        pass

    def generate_batch(self, size: int | None = None) -> list[dict]:
        n = size or self.config.batch_size
        return [self.generate_one() for _ in range(n)]

    def _uuid(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _recent_timestamp(self, hours_back: int = 24) -> str:
        delta = timedelta(
            hours=self._rng.uniform(0, hours_back),
            minutes=self._rng.randint(0, 59),
            seconds=self._rng.randint(0, 59),
        )
        dt = datetime.now(UTC) - delta
        return dt.isoformat()

    def _store_id(self) -> str:
        return f"STR-{self._rng.randint(1, self.config.num_stores):03d}"

    def _customer_phone(self) -> str:
        prefix = self._rng.choice(["09", "03", "07", "08", "05"])
        return f"{prefix}{self._rng.randint(10000000, 99999999)}"

    def _product_id(self) -> str:
        return f"P{self._rng.randint(1, self.config.num_products):04d}"

    def _sku(self) -> str:
        cat = self._rng.choice(["ELEC", "FOOD", "HOME", "CLTH", "HLTH"])
        return f"SKU-{cat}-{self._rng.randint(1, 999):03d}"
