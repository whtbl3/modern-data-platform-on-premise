"""Clickstream generator — web + mobile events (5M/day, peak 600/sec during flash sale)."""
from .base import BaseGenerator, GeneratorConfig

EVENT_TYPES = ["page_view", "click", "scroll", "add_to_cart", "remove_from_cart",
               "search", "purchase", "login", "logout", "signup"]
PAGES = ["/", "/products", "/products/{id}", "/cart", "/checkout",
         "/account", "/search?q={query}", "/category/{cat}", "/flash-sale", "/deals"]
DEVICES = ["desktop", "mobile", "tablet"]
BROWSERS = ["Chrome", "Safari", "Firefox", "Samsung Internet", "Edge"]
OS_LIST = ["Windows", "macOS", "iOS", "Android", "Linux"]
UTM_SOURCES = ["google", "facebook", "instagram", "tiktok", "zalo", "email", "direct", None, None, None]
UTM_CAMPAIGNS = [None, None, None, None, "summer_sale", "flash_sale_aug", "new_user_20", "loyalty_vip", "tet_2025"]
SEARCH_QUERIES = ["iphone", "sua vinamilk", "ao thun", "nuoc rua chen", "tai nghe", "vitamin c", "lock&lock"]
CATEGORIES = ["electronics", "food-beverage", "clothing", "home-living", "health"]


class ClickstreamGenerator(BaseGenerator):
    """Web + Mobile clickstream events for VietMart e-commerce."""

    def __init__(self, config: GeneratorConfig | None = None):
        super().__init__(config)
        self._counter = 0

    def generate_one(self) -> dict:
        self._counter += 1
        is_logged_in = self._rng.random() < 0.55
        session_id = f"sess_{self._rng.randint(100000000, 999999999):09d}"
        page = self._rng.choice(PAGES)

        if "{id}" in page:
            page = page.replace("{id}", str(self._rng.randint(1, self.config.num_products)))
        if "{cat}" in page:
            page = page.replace("{cat}", self._rng.choice(CATEGORIES))
        if "{query}" in page:
            page = page.replace("{query}", self._rng.choice(SEARCH_QUERIES))

        utm_source = self._rng.choice(UTM_SOURCES)

        return {
            "event_id": f"EVT-{self._counter:012d}",
            "session_id": session_id,
            "user_id": f"EC-{self._rng.randint(1, self.config.num_customers):07d}" if is_logged_in else None,
            "event_type": self._rng.choices(
                EVENT_TYPES,
                weights=[30, 20, 15, 8, 3, 10, 4, 5, 3, 2]
            )[0],
            "page_url": page,
            "referrer": self._rng.choice(["google.com", "facebook.com", "direct", "zalo.me", None]),
            "utm_campaign": self._rng.choice(UTM_CAMPAIGNS),
            "utm_source": utm_source,
            "utm_medium": "cpc" if utm_source in ["google", "facebook"] else None,
            "device_type": self._rng.choices(DEVICES, weights=[30, 55, 15])[0],
            "browser": self._rng.choice(BROWSERS),
            "os": self._rng.choice(OS_LIST),
            "country": "VN",
            "city": self._rng.choice(["Ho Chi Minh", "Ha Noi", "Da Nang", "Hai Phong", "Can Tho"]),
            "duration_ms": self._rng.randint(100, 45000),
            "event_time": self._recent_timestamp(hours_back=1),
        }

    def generate_flash_sale_burst(self, events_per_second: int = 600, duration_seconds: int = 10) -> list[dict]:
        """Simulate flash sale traffic spike."""
        total = events_per_second * duration_seconds
        events = []
        for _ in range(total):
            event = self.generate_one()
            event["page_url"] = "/flash-sale"
            event["utm_campaign"] = "flash_sale_aug"
            event["event_type"] = self._rng.choices(
                ["page_view", "add_to_cart", "purchase", "click"],
                weights=[40, 30, 15, 15]
            )[0]
            events.append(event)
        return events
