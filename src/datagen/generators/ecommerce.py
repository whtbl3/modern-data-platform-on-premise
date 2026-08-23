"""E-commerce generators: orders + customers (PostgreSQL CDC source)."""
from .base import BaseGenerator, GeneratorConfig

ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "returned"]
CITIES = ["Ho Chi Minh", "Ha Noi", "Da Nang", "Hai Phong", "Can Tho", "Bien Hoa", "Hue", "Nha Trang"]
FIRST_NAMES = ["Minh", "Linh", "Hoa", "Tuan", "Lan", "Duc", "Mai", "Hung", "Thao", "Nam",
               "An", "Binh", "Chi", "Dung", "Giang", "Ha", "Khanh", "Long", "Ngoc", "Phuong"]
LAST_NAMES = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Vu", "Vo", "Dang", "Bui", "Do"]
REG_SOURCES = ["website", "mobile_app", "facebook", "google", "referral"]


class EcomCustomerGenerator(BaseGenerator):
    """E-commerce registered customers (2M total)."""

    def __init__(self, config: GeneratorConfig | None = None):
        super().__init__(config)
        self._counter = 0

    def generate_one(self) -> dict:
        self._counter += 1
        first = self._rng.choice(FIRST_NAMES)
        last = self._rng.choice(LAST_NAMES)
        phone = self._customer_phone()
        domain = self._rng.choice(["gmail.com", "yahoo.com", "outlook.com", "vietmart.vn"])

        return {
            "customer_id": f"EC-{self._counter:07d}",
            "full_name": f"{last} {first}",
            "email": f"{first.lower()}.{last.lower()}{self._rng.randint(1, 999)}@{domain}",
            "phone": self._rng.choice([f"+84{phone[1:]}", f"0{phone[1:]}", phone]),
            "gender": self._rng.choice(["M", "F", None]),
            "date_of_birth": f"{self._rng.randint(1960, 2005)}-{self._rng.randint(1,12):02d}-{self._rng.randint(1,28):02d}",
            "registration_source": self._rng.choice(REG_SOURCES),
            "created_at": self._recent_timestamp(hours_back=720),
            "updated_at": self._now(),
        }


class EcomOrderGenerator(BaseGenerator):
    """E-commerce orders (50K/day)."""

    def __init__(self, config: GeneratorConfig | None = None):
        super().__init__(config)
        self._counter = 0

    def generate_one(self) -> dict:
        self._counter += 1
        num_items = self._rng.randint(1, 5)
        items = [self._generate_item() for _ in range(num_items)]
        subtotal = sum(i["amount_vnd"] for i in items)
        discount = int(subtotal * self._rng.choice([0, 0, 0.05, 0.1, 0.15, 0.2]))
        shipping = self._rng.choice([0, 15000, 25000, 30000, 50000])
        total = subtotal - discount + shipping

        return {
            "order_id": f"ECOM-{self._counter:08d}",
            "customer_id": f"EC-{self._rng.randint(1, self.config.num_customers):07d}",
            "status": self._rng.choices(ORDER_STATUSES, weights=[5, 10, 15, 20, 40, 7, 3])[0],
            "payment_method": self._rng.choice(["vnpay", "momo", "card", "cod"]),
            "items": items,
            "num_items": num_items,
            "subtotal": subtotal,
            "discount": discount,
            "shipping_fee": shipping,
            "total_amount": total,
            "shipping_address_city": self._rng.choice(CITIES),
            "shipping_address_district": f"District {self._rng.randint(1, 12)}",
            "order_date": self._recent_timestamp(hours_back=24),
            "created_at": self._recent_timestamp(hours_back=24),
            "updated_at": self._now(),
        }

    def _generate_item(self) -> dict:
        qty = self._rng.randint(1, 3)
        price = self._rng.choice([35000, 55000, 89000, 199000, 350000, 990000, 2500000, 6790000, 27990000])
        return {
            "sku": self._sku(),
            "product_id": self._product_id(),
            "quantity": qty,
            "unit_price_vnd": price,
            "amount_vnd": qty * price,
        }
