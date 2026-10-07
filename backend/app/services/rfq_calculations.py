"""
Deterministic Commercial Calculation Engine for RFQ & Quotations.

Adheres strictly to:
- Pure Decimal arithmetic (NEVER float)
- Exact rounding to 2 decimal places for currency totals
- Deterministic quote comparison (lowest unit price, lowest subtotal, lowest landed cost, lead time)
- Explicit currency handling (NO fake FX conversions if currencies differ)
- Zero LLM math / No fabricated duty or tax rates
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Sequence

TWO_PLACES = Decimal("0.01")
FOUR_PLACES = Decimal("0.0001")


def quantize_currency(amount: Decimal | None) -> Decimal:
    """Round monetary amount to 2 decimal places using standard ROUND_HALF_UP."""
    if amount is None:
        return Decimal("0.00")
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def quantize_unit_price(amount: Decimal | None) -> Decimal:
    """Round unit price to 4 decimal places."""
    if amount is None:
        return Decimal("0.0000")
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return amount.quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)


def calculate_line_total(quantity: Decimal, unit_price: Decimal) -> Decimal:
    """
    Calculate line item total: quantity * unit_price.
    Returns Decimal with 2 decimal places.
    """
    if not isinstance(quantity, Decimal):
        quantity = Decimal(str(quantity))
    if not isinstance(unit_price, Decimal):
        unit_price = Decimal(str(unit_price))

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if unit_price < 0:
        raise ValueError("Unit price cannot be negative.")

    raw = quantity * unit_price
    return raw.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_quotation_totals(
    item_line_totals: Sequence[Decimal],
    shipping_cost: Decimal | None = None,
    insurance_cost: Decimal | None = None,
    duty_amount: Decimal | None = None,
    tax_amount: Decimal | None = None,
    other_charges: Decimal | None = None,
) -> tuple[Decimal, Decimal]:
    """
    Deterministic calculation of subtotal and total landed cost.
    
    subtotal = sum(item_line_totals)
    total_landed_cost = subtotal + shipping + insurance + duty + tax + other_charges
    
    Returns: (subtotal_amount, total_landed_cost)
    """
    subtotal = Decimal("0.00")
    for lt in item_line_totals:
        if not isinstance(lt, Decimal):
            lt = Decimal(str(lt))
        if lt < 0:
            raise ValueError("Line total cannot be negative.")
        subtotal += lt

    subtotal = quantize_currency(subtotal)

    # Optional commercial charges
    for name, val in [
        ("shipping_cost", shipping_cost),
        ("insurance_cost", insurance_cost),
        ("duty_amount", duty_amount),
        ("tax_amount", tax_amount),
        ("other_charges", other_charges),
    ]:
        if val is not None and Decimal(str(val)) < 0:
            raise ValueError(f"{name} cannot be negative.")

    shipping = quantize_currency(shipping_cost)
    insurance = quantize_currency(insurance_cost)
    duty = quantize_currency(duty_amount)
    tax = quantize_currency(tax_amount)
    other = quantize_currency(other_charges)

    landed = subtotal + shipping + insurance + duty + tax + other
    return subtotal, quantize_currency(landed)


def build_deterministic_comparison(
    quotations: list[dict[str, Any]],
    rfq_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compare multiple submitted quotations side-by-side.
    
    Identifies:
    - Lowest unit price per RFQ item
    - Lowest subtotal amount
    - Lowest total landed cost
    - Fastest delivery time (lead_time_days)
    - Currency consistency (flags when currencies differ without fake conversion)
    """
    if not quotations:
        return {
            "quotation_count": 0,
            "currency_consistent": True,
            "currency": None,
            "lowest_subtotal_quotation_id": None,
            "lowest_landed_cost_quotation_id": None,
            "fastest_delivery_quotation_id": None,
            "items_comparison": [],
            "quotations": [],
        }

    currencies = {q["currency"] for q in quotations}
    currency_consistent = len(currencies) == 1
    primary_currency = list(currencies)[0] if currency_consistent else "MIXED"

    lowest_subtotal_id = None
    lowest_subtotal_val = None

    lowest_landed_id = None
    lowest_landed_val = None

    fastest_delivery_id = None
    fastest_delivery_days = None

    # Only compare totals directly if currencies are consistent
    for q in quotations:
        q_id = str(q["id"])
        subtotal = Decimal(str(q["subtotal_amount"]))
        landed = Decimal(str(q["total_landed_cost"]))
        lead = q.get("lead_time_days", 0)

        if currency_consistent:
            if lowest_subtotal_val is None or subtotal < lowest_subtotal_val:
                lowest_subtotal_val = subtotal
                lowest_subtotal_id = q_id

            if lowest_landed_val is None or landed < lowest_landed_val:
                lowest_landed_val = landed
                lowest_landed_id = q_id

        if fastest_delivery_days is None or lead < fastest_delivery_days:
            fastest_delivery_days = lead
            fastest_delivery_id = q_id

    # Item-level unit price comparison
    items_comparison = []
    for rfq_item in rfq_items:
        r_item_id = str(rfq_item["id"])
        item_offers = []

        lowest_unit_price_val = None
        lowest_unit_price_quote_id = None

        for q in quotations:
            # find matching quotation item
            matched_q_item = next(
                (qi for qi in q.get("items", []) if str(qi.get("rfq_item_id")) == r_item_id),
                None,
            )
            if matched_q_item:
                u_price = Decimal(str(matched_q_item["unit_price"]))
                item_offers.append({
                    "quotation_id": str(q["id"]),
                    "supplier_name": q.get("supplier_name", "Supplier"),
                    "unit_price": u_price,
                    "currency": q["currency"],
                    "line_total": Decimal(str(matched_q_item["line_total"])),
                    "lead_time_days": matched_q_item.get("lead_time_days"),
                    "moq": matched_q_item.get("moq"),
                })
                if currency_consistent:
                    if lowest_unit_price_val is None or u_price < lowest_unit_price_val:
                        lowest_unit_price_val = u_price
                        lowest_unit_price_quote_id = str(q["id"])
            else:
                item_offers.append({
                    "quotation_id": str(q["id"]),
                    "supplier_name": q.get("supplier_name", "Supplier"),
                    "unit_price": None,
                    "currency": q["currency"],
                    "line_total": None,
                    "lead_time_days": None,
                    "moq": None,
                })

        items_comparison.append({
            "rfq_item_id": r_item_id,
            "product_name": rfq_item.get("product_name_snapshot"),
            "requested_quantity": Decimal(str(rfq_item.get("quantity"))),
            "unit": rfq_item.get("unit"),
            "lowest_unit_price_quotation_id": lowest_unit_price_quote_id,
            "offers": item_offers,
        })

    return {
        "quotation_count": len(quotations),
        "currency_consistent": currency_consistent,
        "currency": primary_currency,
        "lowest_subtotal_quotation_id": lowest_subtotal_id,
        "lowest_landed_cost_quotation_id": lowest_landed_id,
        "fastest_delivery_quotation_id": fastest_delivery_id,
        "items_comparison": items_comparison,
        "quotations": quotations,
    }
