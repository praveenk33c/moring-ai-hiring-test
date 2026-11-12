"""Turn the strings the model copies off the page into Python values."""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal

from dateutil import parser as dateparser

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CURRENCY_RE = re.compile(r"(?i)\b(?:INR|USD|EUR|GBP|RS)\.?|[₹$€£]")
_CRORE_RE = re.compile(r"(?i)\b(?:crores?|cr)\.?(\b|$)")
_LAKH_RE = re.compile(r"(?i)\b(?:lakhs?|lacs?)\b")


def parse_amount(value) -> float | None:
    """Parse Indian and international amount strings ('₹ 1,23,456.00', 'Rs. 1,23,456/-', '₹1.2 lakh') -> float."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None

    multiplier = Decimal("1")
    if _CRORE_RE.search(text):
        multiplier = Decimal("10000000")
        text = _CRORE_RE.sub("", text)
    elif _LAKH_RE.search(text):
        multiplier = Decimal("100000")
        text = _LAKH_RE.sub("", text)

    cleaned = _CURRENCY_RE.sub("", text).replace(",", "").strip()
    cleaned = re.sub(r"[/\-=]+$", "", cleaned).strip()

    negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        negative = True
        cleaned = cleaned[1:-1].strip()

    if not cleaned:
        return None

    amount = Decimal(cleaned) * multiplier
    if negative and amount > 0:
        amount = -amount
    return float(amount)


def parse_date(value, *, country: str = "IN") -> date | None:
    """Accept whatever date format the vendor printed (day-first for IN, month-first for US)."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    if _ISO_DATE_RE.fullmatch(text):
        return date.fromisoformat(text)
    dayfirst = (country or "IN").strip().upper() != "US"
    return dateparser.parse(text, dayfirst=dayfirst).date()
