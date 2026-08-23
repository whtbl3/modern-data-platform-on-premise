"""
Tests that shared business rules generate correct SQL
and stay consistent between batch/streaming definitions.
"""
from src.shared_logic.rules import (
    CANCELLED_STATUSES,
    COMPLETED_STATUSES,
    INVENTORY_ALERT_RULES,
    ORDER_VALIDATIONS,
    PAYMENT_RECONCILIATION_THRESHOLD_PCT,
    REVENUE_DAILY,
    RFM_SEGMENTS,
)
from src.shared_logic.sql_templates import (
    inventory_alert_case_sql,
    is_cancelled_sql,
    is_completed_sql,
    order_filter_sql,
    phone_normalize_sql,
    reconciliation_alert_sql,
    revenue_aggregation_sql,
)


class TestOrderRules:
    def test_filter_includes_all_validations(self):
        sql = order_filter_sql()
        for rule in ORDER_VALIDATIONS:
            assert rule.field in sql

    def test_completed_statuses(self):
        sql = is_completed_sql()
        for status in COMPLETED_STATUSES:
            assert status in sql

    def test_cancelled_statuses(self):
        sql = is_cancelled_sql()
        for status in CANCELLED_STATUSES:
            assert status in sql

    def test_filter_produces_valid_sql_fragment(self):
        sql = order_filter_sql()
        assert "AND" in sql
        assert "IS NOT NULL" in sql
        assert "> 0" in sql


class TestRevenueAggregation:
    def test_has_required_metrics(self):
        assert "order_count" in REVENUE_DAILY.metrics
        assert "gross_revenue" in REVENUE_DAILY.metrics
        assert "net_revenue" in REVENUE_DAILY.metrics

    def test_sql_generation(self):
        sql = revenue_aggregation_sql(source="my_table", where="status = 'completed'")
        assert "my_table" in sql
        assert "GROUP BY" in sql
        assert "status = 'completed'" in sql

    def test_group_by_fields(self):
        assert "revenue_date" in REVENUE_DAILY.group_by
        assert "store_id" in REVENUE_DAILY.group_by
        assert "channel" in REVENUE_DAILY.group_by


class TestInventoryAlerts:
    def test_alert_types_defined(self):
        assert "out_of_stock" in INVENTORY_ALERT_RULES
        assert "low_stock" in INVENTORY_ALERT_RULES
        assert "reorder" in INVENTORY_ALERT_RULES

    def test_case_sql(self):
        sql = inventory_alert_case_sql()
        assert "OUT_OF_STOCK" in sql
        assert "LOW_STOCK" in sql
        assert "REORDER" in sql
        assert "CASE" in sql


class TestReconciliation:
    def test_threshold_is_reasonable(self):
        assert 0 < PAYMENT_RECONCILIATION_THRESHOLD_PCT <= 5.0

    def test_alert_sql(self):
        sql = reconciliation_alert_sql()
        assert "CRITICAL" in sql
        assert "WARNING" in sql
        assert "OK" in sql


class TestPhoneNormalization:
    def test_sql_handles_plus84(self):
        sql = phone_normalize_sql("phone")
        assert "+84" in sql
        assert "SUBSTR" in sql

    def test_sql_handles_spaces(self):
        sql = phone_normalize_sql("phone")
        assert "REPLACE" in sql


class TestRFMSegments:
    def test_all_segments_defined(self):
        expected = ["Champion", "Loyal", "New", "At Risk", "Hibernating", "Lost"]
        for segment in expected:
            assert segment in RFM_SEGMENTS

    def test_segment_bounds_valid(self):
        for segment, rules in RFM_SEGMENTS.items():
            for dimension in ["recency", "frequency", "monetary"]:
                low, high = rules[dimension]
                assert 1 <= low <= high <= 5
