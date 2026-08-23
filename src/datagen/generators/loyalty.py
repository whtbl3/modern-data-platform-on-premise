"""Loyalty program member generator — 1.5M members (MySQL CDC source)."""
from .base import BaseGenerator, GeneratorConfig

TIERS = ["Bronze", "Silver", "Gold", "Platinum"]
FIRST_NAMES = ["Minh", "Linh", "Hoa", "Tuan", "Lan", "Duc", "Mai", "Hung", "Thao", "Nam"]
LAST_NAMES = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Vu", "Vo", "Dang", "Bui", "Do"]


class LoyaltyMemberGenerator(BaseGenerator):
    """Loyalty program members — phone format intentionally inconsistent (reflects real data)."""

    def __init__(self, config: GeneratorConfig | None = None):
        super().__init__(config)
        self._counter = 0

    def generate_one(self) -> dict:
        self._counter += 1
        first = self._rng.choice(FIRST_NAMES)
        last = self._rng.choice(LAST_NAMES)
        phone_raw = self._customer_phone()

        # Intentionally inconsistent phone formats (real-world quality issue)
        phone_formats = [
            phone_raw,                          # 0912345678
            f"+84{phone_raw[1:]}",             # +84912345678
            f"84{phone_raw[1:]}",              # 84912345678
            f"{phone_raw[:4]} {phone_raw[4:7]} {phone_raw[7:]}",  # 0912 345 678
        ]

        tier = self._rng.choices(TIERS, weights=[50, 30, 15, 5])[0]
        points = {
            "Bronze": self._rng.randint(0, 999),
            "Silver": self._rng.randint(1000, 4999),
            "Gold": self._rng.randint(5000, 19999),
            "Platinum": self._rng.randint(20000, 100000),
        }[tier]

        return {
            "member_id": f"LYL-{self._counter:07d}",
            "full_name": f"{last} {first}",
            "email": f"{first.lower()}{self._rng.randint(1, 999)}@{self._rng.choice(['gmail.com', 'yahoo.com'])}",
            "phone": self._rng.choice(phone_formats),
            "tier": tier,
            "points_balance": points,
            "joined_date": self._recent_timestamp(hours_back=8760),  # up to 1 year ago
            "last_activity_date": self._recent_timestamp(hours_back=720),  # last 30 days
            "updated_at": self._now(),
        }
