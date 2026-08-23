"""
Shared business rules — single source of truth for both batch and streaming.

These rules define WHAT the logic is. Each engine (dbt, Flink, Spark)
implements HOW to execute it.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationRule:
    field: str
    condition: str
    description: str


@dataclass(frozen=True)
class AggregationRule:
    name: str
    group_by: list[str]
    metrics: dict[str, str]
    description: str


# --- ORDER VALIDATION (POS + e-commerce) ---
ORDER_VALIDATIONS = [
    ValidationRule("order_id", "IS NOT NULL", "Order must have an ID"),
    ValidationRule("customer_id", "IS NOT NULL", "Order must have a customer"),
    ValidationRule("amount", "> 0", "Amount must be positive"),
]

VALID_ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "returned"]
COMPLETED_STATUSES = ["delivered", "completed"]
CANCELLED_STATUSES = ["cancelled", "returned"]

# --- REVENUE AGGREGATION ---
REVENUE_DAILY = AggregationRule(
    name="revenue_daily",
    group_by=["revenue_date", "store_id", "channel"],
    metrics={
        "order_count": "COUNT(*)",
        "gross_revenue": "SUM(amount)",
        "net_revenue": "SUM(amount - discount)",
        "avg_order_value": "AVG(amount)",
    },
    description="Daily revenue metrics by store and channel",
)

# --- PAYMENT GATEWAY RULES ---
PAYMENT_SUCCESS_CODES = {
    "vnpay": ["00"],
    "momo": [0],
    "card": ["SETTLED"],
}

PAYMENT_RECONCILIATION_THRESHOLD_PCT = 1.0

# --- INVENTORY RULES ---
INVENTORY_ALERT_RULES = {
    "out_of_stock": {"condition": "qty_available <= 0"},
    "low_stock": {"condition": "qty_available <= safety_stock"},
    "reorder": {"condition": "qty_available <= reorder_point"},
}

# --- CUSTOMER SEGMENTATION (RFM) ---
RFM_SEGMENTS = {
    "Champion": {"recency": (1, 2), "frequency": (4, 5), "monetary": (4, 5)},
    "Loyal": {"recency": (2, 4), "frequency": (3, 5), "monetary": (3, 5)},
    "New": {"recency": (1, 1), "frequency": (1, 1), "monetary": (1, 5)},
    "At Risk": {"recency": (3, 5), "frequency": (3, 5), "monetary": (3, 5)},
    "Hibernating": {"recency": (4, 5), "frequency": (1, 2), "monetary": (1, 2)},
    "Lost": {"recency": (5, 5), "frequency": (1, 5), "monetary": (1, 5)},
}

# --- CLICKSTREAM RULES ---
CONVERSION_EVENTS = ["purchase"]
ENGAGEMENT_EVENTS = ["page_view", "click", "scroll", "add_to_cart", "search"]
SESSION_TIMEOUT_MINUTES = 30
FLASH_SALE_PAGE = "/flash-sale"

# --- PHONE NORMALIZATION (Vietnam) ---
PHONE_NORMALIZE_RULES = {
    "remove_prefix_+84": "+84 → 0",
    "remove_prefix_84": "84 → 0",
    "strip_spaces": "Remove all spaces",
    "strip_dashes": "Remove all dashes",
}
