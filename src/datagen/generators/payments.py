"""Payment gateway generators: VNPay, Momo, Card (3 different formats)."""
from .base import BaseGenerator, GeneratorConfig

BANKS = ["VCB", "TCB", "ACB", "MB", "BIDV", "VPB", "TPB", "STB"]


class PaymentGenerator(BaseGenerator):
    """Generates payment transactions for all 3 gateways."""

    def __init__(self, config: GeneratorConfig | None = None):
        super().__init__(config)
        self._counter = 0

    def generate_one(self) -> dict:
        gateway = self._rng.choices(
            ["vnpay", "momo", "card"],
            weights=[45, 25, 30]
        )[0]

        if gateway == "vnpay":
            return self._generate_vnpay()
        elif gateway == "momo":
            return self._generate_momo()
        else:
            return self._generate_card()

    def generate_vnpay_batch(self, size: int) -> list[dict]:
        return [self._generate_vnpay() for _ in range(size)]

    def generate_momo_batch(self, size: int) -> list[dict]:
        return [self._generate_momo() for _ in range(size)]

    def generate_card_batch(self, size: int) -> list[dict]:
        return [self._generate_card() for _ in range(size)]

    def _generate_vnpay(self) -> dict:
        self._counter += 1
        amount = self._rng.randint(50000, 30000000)
        is_success = self._rng.random() < 0.92

        return {
            "_gateway": "vnpay",
            "vnp_txn_ref": f"VNP{self._counter:010d}",
            "vnp_order_info": f"ECOM-{self._rng.randint(1, 500000):08d}",
            "vnp_amount": amount,
            "vnp_response_code": "00" if is_success else self._rng.choice(["07", "09", "12", "24"]),
            "vnp_bank_code": self._rng.choice(BANKS),
            "vnp_pay_date": self._recent_timestamp(hours_back=24),
        }

    def _generate_momo(self) -> dict:
        self._counter += 1
        amount = self._rng.randint(30000, 20000000)
        is_success = self._rng.random() < 0.90

        return {
            "_gateway": "momo",
            "trans_id": f"MOMO{self._counter:010d}",
            "order_id": f"ECOM-{self._rng.randint(1, 500000):08d}",
            "amount": amount,
            "result_code": 0 if is_success else self._rng.choice([1006, 1005, 1004]),
            "response_time": self._recent_timestamp(hours_back=24),
        }

    def _generate_card(self) -> dict:
        self._counter += 1
        gross = self._rng.randint(100000, 50000000)
        fee = int(gross * 0.022)
        is_settled = self._rng.random() < 0.88

        return {
            "_gateway": "card",
            "transaction_id": f"CARD{self._counter:010d}",
            "merchant_ref": f"ECOM-{self._rng.randint(1, 500000):08d}",
            "gross_amount": gross,
            "fee": fee,
            "status": "SETTLED" if is_settled else self._rng.choice(["DECLINED", "PENDING", "REFUNDED"]),
            "issuer_bank": self._rng.choice(BANKS),
            "settled_at": self._recent_timestamp(hours_back=48),
        }
