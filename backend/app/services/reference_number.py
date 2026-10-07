"""
Collision-safe reference number generator for RFQs and Quotations.

Adheres to:
- No unsafe 'count rows + 1' pattern (which suffers from race conditions under concurrency)
- Formatted human-readable strings: RFQ-YYYY-XXXXXX and QT-YYYY-XXXXXX
- Cryptographic entropy + database collision-detection retry loop
"""
import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.rfq import RFQ
from app.models.quotation import Quotation


def generate_rfq_number(db: Session, max_retries: int = 5) -> str:
    """
    Generate a unique, collision-safe RFQ reference number.
    Format: RFQ-<YEAR>-<6 HEX CHARS> (e.g. RFQ-2026-8A3F1B)
    """
    year = datetime.now(timezone.utc).year
    for _ in range(max_retries):
        token = secrets.token_hex(3).upper()  # 6 characters, ~16.7 million combinations per year
        candidate = f"RFQ-{year}-{token}"
        existing = db.query(RFQ.id).filter_by(rfq_number=candidate).first()
        if existing is None:
            return candidate

    # Fallback with higher entropy if collision occurred repeatedly
    return f"RFQ-{year}-{secrets.token_hex(6).upper()}"


def generate_quotation_number(db: Session, max_retries: int = 5) -> str:
    """
    Generate a unique, collision-safe Quotation reference number.
    Format: QT-<YEAR>-<6 HEX CHARS> (e.g. QT-2026-9C4D2E)
    """
    year = datetime.now(timezone.utc).year
    for _ in range(max_retries):
        token = secrets.token_hex(3).upper()
        candidate = f"QT-{year}-{token}"
        existing = db.query(Quotation.id).filter_by(quotation_number=candidate).first()
        if existing is None:
            return candidate

    return f"QT-{year}-{secrets.token_hex(6).upper()}"
