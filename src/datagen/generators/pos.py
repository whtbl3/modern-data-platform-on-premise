"""POS Transaction Generator — 120 stores, 800K txn/day."""
from .base import BaseGenerator, GeneratorConfig

PAYMENT_METHODS = ["cash", "card", "vnpay_qr", "momo_qr", "bank_transfer"]


class POSTransactionGenerator(BaseGenerator):
    """Simulates POS CSV export from Oracle POS system (120 stores)."""

    def __init__(self, config: GeneratorConfig | None = None):
        super().__init__(config)
        self._txn_counter = 0

    def generate_one(self) -> dict:
        self._txn_counter += 1
        store_id = self._store_id()
        num_items = self._rng.randint(1, 8)
        items = [self._generate_item() for _ in range(num_items)]
        subtotal = sum(item["amount_vnd"] for item in items)
        discount = int(subtotal * self._rng.choice([0, 0, 0, 0.05, 0.1, 0.15]))
        tax = int(subtotal * 0.1)
        total = subtotal - discount + tax

        has_customer = self._rng.random() < 0.6

        return {
            "txn_id": f"POS-{store_id}-{self._txn_counter:08d}",
            "store_id": store_id,
            "cashier_id": f"EMP-{store_id}-{self._rng.randint(1, 15):02d}",
            "customer_phone": self._customer_phone() if has_customer else None,
            "items": items,
            "num_items": num_items,
            "subtotal": subtotal,
            "discount_amount": discount,
            "tax_amount": tax,
            "total_amount": total,
            "payment_method": self._rng.choice(PAYMENT_METHODS),
            "txn_timestamp": self._recent_timestamp(hours_back=24),
        }

    def _generate_item(self) -> dict:
        qty = self._rng.randint(1, 5)
        unit_price = self._rng.choice([
            15000, 25000, 35000, 55000, 89000, 120000, 199000, 350000,
            550000, 990000, 2500000, 5990000, 15990000, 27990000,
        ])
        return {
            "sku": self._sku(),
            "product_id": self._product_id(),
            "quantity": qty,
            "unit_price_vnd": unit_price,
            "amount_vnd": qty * unit_price,
        }
