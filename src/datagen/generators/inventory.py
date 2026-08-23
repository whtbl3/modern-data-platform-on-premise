"""Inventory generator — SAP stock level exports (50K SKUs × 120 stores)."""
from .base import BaseGenerator, GeneratorConfig


class InventoryGenerator(BaseGenerator):
    """Simulates SAP inventory snapshot export (every 30 min)."""

    def __init__(self, config: GeneratorConfig | None = None):
        super().__init__(config)

    def generate_one(self) -> dict:
        qty_on_hand = self._rng.randint(0, 500)
        qty_reserved = self._rng.randint(0, min(qty_on_hand, 50))
        safety_stock = self._rng.choice([5, 10, 20, 30, 50])
        reorder_point = safety_stock * 2

        return {
            "store_id": self._store_id(),
            "sku": self._sku(),
            "product_id": self._product_id(),
            "quantity_on_hand": qty_on_hand,
            "quantity_reserved": qty_reserved,
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "snapshot_time": self._recent_timestamp(hours_back=1),
        }

    def generate_store_snapshot(self, store_id: str, num_skus: int = 200) -> list[dict]:
        """Generate a full inventory snapshot for a single store."""
        records = []
        for _ in range(num_skus):
            record = self.generate_one()
            record["store_id"] = store_id
            records.append(record)
        return records
