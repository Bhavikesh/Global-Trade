"""
Unit tests for deterministic commercial calculations in app.services.rfq_calculations.
"""
from decimal import Decimal
import pytest

from app.services.rfq_calculations import (
    calculate_line_total,
    calculate_quotation_totals,
    build_deterministic_comparison,
    quantize_currency,
    quantize_unit_price,
)


class TestCalculationEngine:
    def test_line_total_decimal_precision(self):
        # 123.4567 * 3.5 = 432.09845 -> rounds to 432.10
        total = calculate_line_total(Decimal("3.5"), Decimal("123.4567"))
        assert total == Decimal("432.10")

    def test_line_total_validation(self):
        with pytest.raises(ValueError, match="Quantity must be greater than zero"):
            calculate_line_total(Decimal("0.00"), Decimal("10.00"))

        with pytest.raises(ValueError, match="Quantity must be greater than zero"):
            calculate_line_total(Decimal("-5.00"), Decimal("10.00"))

        with pytest.raises(ValueError, match="Unit price cannot be negative"):
            calculate_line_total(Decimal("10.00"), Decimal("-1.00"))

    def test_quotation_totals_with_all_charges(self):
        item_totals = [Decimal("100.25"), Decimal("200.50"), Decimal("300.00")]
        subtotal, landed = calculate_quotation_totals(
            item_line_totals=item_totals,
            shipping_cost=Decimal("50.00"),
            insurance_cost=Decimal("15.50"),
            duty_amount=Decimal("25.00"),
            tax_amount=Decimal("30.75"),
            other_charges=Decimal("10.00"),
        )
        assert subtotal == Decimal("600.75")
        # 600.75 + 50 + 15.50 + 25 + 30.75 + 10 = 732.00
        assert landed == Decimal("732.00")

    def test_quotation_totals_zero_and_none_charges(self):
        item_totals = [Decimal("500.00")]
        subtotal, landed = calculate_quotation_totals(
            item_line_totals=item_totals,
            shipping_cost=None,
            insurance_cost=None,
            duty_amount=None,
            tax_amount=None,
            other_charges=None,
        )
        assert subtotal == Decimal("500.00")
        assert landed == Decimal("500.00")

    def test_quotation_totals_negative_charge_rejected(self):
        with pytest.raises(ValueError, match="shipping_cost cannot be negative"):
            calculate_quotation_totals(
                item_line_totals=[Decimal("100.00")],
                shipping_cost=Decimal("-10.00"),
            )

    def test_comparison_mixed_currencies_flagged(self):
        quotes = [
            {
                "id": "q-usd",
                "currency": "USD",
                "subtotal_amount": "1000.00",
                "total_landed_cost": "1100.00",
                "lead_time_days": 10,
                "items": [],
            },
            {
                "id": "q-eur",
                "currency": "EUR",
                "subtotal_amount": "950.00",
                "total_landed_cost": "1050.00",
                "lead_time_days": 12,
                "items": [],
            },
        ]
        res = build_deterministic_comparison(quotes, [])
        assert res["currency_consistent"] is False
        assert res["currency"] == "MIXED"
        # When currencies differ, lowest totals are NOT calculated (no fake FX rate)
        assert res["lowest_subtotal_quotation_id"] is None
        assert res["lowest_landed_cost_quotation_id"] is None
        # Operational comparison (lead time) still works
        assert res["fastest_delivery_quotation_id"] == "q-usd"
