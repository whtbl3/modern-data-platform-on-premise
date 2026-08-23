"""Tests for VietMart data generators."""
import pytest

from src.datagen.generators import (
    ClickstreamGenerator,
    EcomCustomerGenerator,
    EcomOrderGenerator,
    GeneratorConfig,
    InventoryGenerator,
    LoyaltyMemberGenerator,
    PaymentGenerator,
    POSTransactionGenerator,
)


@pytest.fixture
def config():
    return GeneratorConfig(seed=42)


class TestPOSTransactionGenerator:
    def test_generate_one(self, config):
        gen = POSTransactionGenerator(config)
        record = gen.generate_one()

        assert record["txn_id"].startswith("POS-STR-")
        assert record["store_id"].startswith("STR-")
        assert record["total_amount"] > 0
        assert record["payment_method"] in ["cash", "card", "vnpay_qr", "momo_qr", "bank_transfer"]
        assert len(record["items"]) >= 1

    def test_line_item_totals(self, config):
        gen = POSTransactionGenerator(config)
        record = gen.generate_one()

        for item in record["items"]:
            expected = item["quantity"] * item["unit_price_vnd"]
            assert item["amount_vnd"] == expected

    def test_batch_deterministic(self):
        gen1 = POSTransactionGenerator(GeneratorConfig(seed=99))
        gen2 = POSTransactionGenerator(GeneratorConfig(seed=99))

        r1 = gen1.generate_one()
        r2 = gen2.generate_one()
        assert r1["store_id"] == r2["store_id"]
        assert r1["total_amount"] == r2["total_amount"]

    def test_batch_size(self, config):
        gen = POSTransactionGenerator(config)
        batch = gen.generate_batch(100)
        assert len(batch) == 100
        ids = {r["txn_id"] for r in batch}
        assert len(ids) == 100


class TestEcomOrderGenerator:
    def test_generate_one(self, config):
        gen = EcomOrderGenerator(config)
        record = gen.generate_one()

        assert record["order_id"].startswith("ECOM-")
        assert record["customer_id"].startswith("EC-")
        assert record["total_amount"] > 0
        assert record["status"] in [
            "pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "returned"
        ]
        assert record["payment_method"] in ["vnpay", "momo", "card", "cod"]

    def test_batch_unique_ids(self, config):
        gen = EcomOrderGenerator(config)
        batch = gen.generate_batch(200)
        ids = {r["order_id"] for r in batch}
        assert len(ids) == 200


class TestEcomCustomerGenerator:
    def test_generate_one(self, config):
        gen = EcomCustomerGenerator(config)
        record = gen.generate_one()

        assert record["customer_id"].startswith("EC-")
        assert "@" in record["email"]
        assert record["phone"].startswith("0") or record["phone"].startswith("+84")

    def test_phone_formats(self, config):
        gen = EcomCustomerGenerator(config)
        batch = gen.generate_batch(100)
        phones = [r["phone"] for r in batch]
        has_0_prefix = any(p.startswith("0") for p in phones)
        has_84_prefix = any(p.startswith("+84") for p in phones)
        assert has_0_prefix or has_84_prefix


class TestPaymentGenerator:
    def test_generate_one(self, config):
        gen = PaymentGenerator(config)
        record = gen.generate_one()

        assert record["_gateway"] in ["vnpay", "momo", "card"]

    def test_vnpay_format(self, config):
        gen = PaymentGenerator(config)
        batch = gen.generate_vnpay_batch(50)

        for record in batch:
            assert record["_gateway"] == "vnpay"
            assert record["vnp_txn_ref"].startswith("VNP")
            assert record["vnp_amount"] > 0

    def test_momo_format(self, config):
        gen = PaymentGenerator(config)
        batch = gen.generate_momo_batch(50)

        for record in batch:
            assert record["_gateway"] == "momo"
            assert record["trans_id"].startswith("MOMO")
            assert record["amount"] > 0

    def test_card_format(self, config):
        gen = PaymentGenerator(config)
        batch = gen.generate_card_batch(50)

        for record in batch:
            assert record["_gateway"] == "card"
            assert record["transaction_id"].startswith("CARD")
            assert record["gross_amount"] > 0
            assert record["fee"] == int(record["gross_amount"] * 0.022)


class TestInventoryGenerator:
    def test_generate_one(self, config):
        gen = InventoryGenerator(config)
        record = gen.generate_one()

        assert record["store_id"].startswith("STR-")
        assert record["sku"].startswith("SKU-")
        assert record["quantity_on_hand"] >= 0
        assert record["quantity_reserved"] <= record["quantity_on_hand"]
        assert record["safety_stock"] > 0

    def test_store_snapshot(self, config):
        gen = InventoryGenerator(config)
        snapshot = gen.generate_store_snapshot("STR-001", num_skus=50)

        assert len(snapshot) == 50
        assert all(r["store_id"] == "STR-001" for r in snapshot)


class TestLoyaltyMemberGenerator:
    def test_generate_one(self, config):
        gen = LoyaltyMemberGenerator(config)
        record = gen.generate_one()

        assert record["member_id"].startswith("LYL-")
        assert record["tier"] in ["Bronze", "Silver", "Gold", "Platinum"]
        assert record["points_balance"] >= 0
        assert "@" in record["email"]

    def test_inconsistent_phone_formats(self, config):
        gen = LoyaltyMemberGenerator(config)
        batch = gen.generate_batch(200)
        phones = [r["phone"] for r in batch]

        formats_seen = set()
        for p in phones:
            if p.startswith("+84"):
                formats_seen.add("+84")
            elif p.startswith("84") and not p.startswith("+"):
                formats_seen.add("84")
            elif " " in p:
                formats_seen.add("spaced")
            else:
                formats_seen.add("plain")

        assert len(formats_seen) >= 2  # at least 2 different formats

    def test_tier_distribution(self, config):
        gen = LoyaltyMemberGenerator(config)
        batch = gen.generate_batch(1000)
        tiers = [r["tier"] for r in batch]
        bronze_count = tiers.count("Bronze")
        platinum_count = tiers.count("Platinum")
        assert bronze_count > platinum_count  # Bronze should be most common


class TestClickstreamGenerator:
    def test_generate_one(self, config):
        gen = ClickstreamGenerator(config)
        record = gen.generate_one()

        assert record["event_id"].startswith("EVT-")
        assert record["session_id"].startswith("sess_")
        assert record["event_type"] in [
            "page_view", "click", "scroll", "add_to_cart", "remove_from_cart",
            "search", "purchase", "login", "logout", "signup",
        ]
        assert record["duration_ms"] > 0
        assert record["country"] == "VN"

    def test_anonymous_users(self, config):
        gen = ClickstreamGenerator(config)
        batch = gen.generate_batch(1000)
        anonymous = sum(1 for r in batch if r["user_id"] is None)
        # ~45% anonymous (1 - 0.55)
        assert 300 < anonymous < 600

    def test_flash_sale_burst(self, config):
        gen = ClickstreamGenerator(config)
        events = gen.generate_flash_sale_burst(events_per_second=10, duration_seconds=2)

        assert len(events) == 20
        assert all(e["page_url"] == "/flash-sale" for e in events)
        assert all(e["utm_campaign"] == "flash_sale_aug" for e in events)

    def test_mobile_heavy(self, config):
        gen = ClickstreamGenerator(config)
        batch = gen.generate_batch(1000)
        mobile = sum(1 for r in batch if r["device_type"] == "mobile")
        # Mobile weight is 55%
        assert mobile > 400
