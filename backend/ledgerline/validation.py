"""Deterministic checks.

Since v0.3 these are informational: they are stored as `warnings` and shown to reviewers.
Routing is decided by the model, which applies the AP policy itself (see pipeline.py).
"""
from __future__ import annotations

import re
import sqlite3
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from itertools import product as iter_product

from .models import Invoice
from .reference import ReferenceData

GSTIN_PATTERN = re.compile(r"\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]")
GSTIN_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BUYER_STATE_CODE = "27"  # Maharashtra


def _to_dec(value: float | str | Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def gstin_checksum(first14: str) -> str:
    total = 0
    for i, ch in enumerate(first14):
        product = GSTIN_ALPHABET.index(ch) * (1 if i % 2 == 0 else 2)
        total += product // 36 + product % 36
    return GSTIN_ALPHABET[(36 - total % 36) % 36]


def is_valid_gstin(gstin: str | None) -> bool:
    """Validate a GSTIN's format and check digit."""
    if not gstin:
        return False
    cleaned = gstin.strip().upper()
    if GSTIN_PATTERN.fullmatch(cleaned) is None:
        return False
    return gstin_checksum(cleaned[:14]) == cleaned[14]


_DIGIT_POSITIONS = {0, 1, 7, 8, 9, 10}
_LETTER_POSITIONS = {2, 3, 4, 5, 6, 11, 13}
_LETTER_TO_DIGIT_OPTIONS: dict[str, tuple[str, ...]] = {
    "O": ("0",),
    "Q": ("0",),
    "D": ("0",),
    "I": ("1",),
    "L": ("1",),
    "Z": ("2",),
    "S": ("5",),
    "G": ("6",),
    "B": ("8",),
}
_DIGIT_TO_LETTER_OPTIONS: dict[str, tuple[str, ...]] = {
    "0": ("O", "D", "Q"),
    "1": ("I", "L"),
    "2": ("Z",),
    "5": ("S",),
    "6": ("G",),
    "8": ("B",),
}


def repair_ocr_gstin(gstin: str | None, ref: ReferenceData) -> str | None:
    """Deterministically repair OCR letter<->digit lookalikes in a 15-char GSTIN.

    A candidate is accepted ONLY if it (1) matches a known vendor GSTIN in ref.vendors
    and (2) passes structural + Appendix A checksum validation (is_valid_gstin).
    Otherwise returns None so the document is flagged and routed to human review.
    """
    if not gstin:
        return None
    cleaned = gstin.strip().upper()
    if len(cleaned) != 15:
        return None
    known_gstins = {
        (v.get("gstin") or "").strip().upper()
        for v in ref.vendors
        if (v.get("gstin") or "").strip()
    }
    if cleaned in known_gstins and is_valid_gstin(cleaned):
        return cleaned

    char_choices: list[tuple[str, ...]] = []
    for idx, ch in enumerate(cleaned):
        if idx in _DIGIT_POSITIONS:
            alts = _LETTER_TO_DIGIT_OPTIONS.get(ch, ())
        elif idx in _LETTER_POSITIONS:
            alts = _DIGIT_TO_LETTER_OPTIONS.get(ch, ())
        else:
            alts = _LETTER_TO_DIGIT_OPTIONS.get(ch, ()) + _DIGIT_TO_LETTER_OPTIONS.get(ch, ())
        # Try OCR replacement(s) as well as keeping original character
        seen: list[str] = []
        for candidate_ch in (ch, *alts):
            if candidate_ch not in seen:
                seen.append(candidate_ch)
        char_choices.append(tuple(seen))

    for combo in iter_product(*char_choices):
        candidate = "".join(combo)
        if candidate == cleaned:
            continue
        if candidate in known_gstins and is_valid_gstin(candidate):
            return candidate
    return None


def _norm_legal_name(name: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def supplier_key(inv: Invoice) -> str | None:
    """Supplier key per AP Policy Section 1: GSTIN for domestic (INR), normalized legal name for foreign."""
    if (inv.currency or "INR").upper() == "INR":
        gstin = (inv.supplier_gstin or "").strip().upper()
        return gstin or None
    key = _norm_legal_name(inv.supplier_name)
    return key or None


def find_vendor(ref: ReferenceData, inv_or_name: Invoice | str | None) -> dict | None:
    if inv_or_name is None:
        return None
    if isinstance(inv_or_name, Invoice):
        key = supplier_key(inv_or_name)
        if not key:
            return None
        if (inv_or_name.currency or "INR").upper() == "INR":
            for vendor in ref.vendors:
                if (vendor.get("gstin") or "").strip().upper() == key:
                    return vendor
            return None
        for vendor in ref.vendors:
            if _norm_legal_name(vendor.get("legal_name")) == key:
                return vendor
        return None

    # Fallback when called with a string (GSTIN or legal name) in legacy callers/tests
    raw = str(inv_or_name).strip()
    if not raw:
        return None
    upper = raw.upper()
    for vendor in ref.vendors:
        if (vendor.get("gstin") or "").strip().upper() == upper:
            return vendor
    norm = _norm_legal_name(raw)
    for vendor in ref.vendors:
        if _norm_legal_name(vendor.get("legal_name")) == norm:
            return vendor
    return None


def check_credit_note(inv: Invoice) -> list[str]:
    if (inv.document_type or "invoice").strip().lower() == "credit_note":
        return ["credit_note"]
    return []


def check_vendor(vendor: dict | None) -> list[str]:
    return [] if vendor else ["vendor_unknown"]


def check_vendor_new(inv: Invoice, vendor: dict | None) -> list[str]:
    if not vendor or not inv.invoice_date:
        return []
    raw_onboarded = (vendor.get("onboarded_on") or "").strip()
    if not raw_onboarded:
        return []
    try:
        onboarded_date = date.fromisoformat(raw_onboarded[:10])
    except ValueError:
        return []
    if (inv.invoice_date - onboarded_date).days < 90:
        return ["vendor_new"]
    return []


def check_foreign_currency(inv: Invoice) -> list[str]:
    if (inv.currency or "INR").strip().upper() != "INR":
        return ["foreign_currency"]
    return []


def check_gstin(inv: Invoice) -> list[str]:
    if inv.currency == "INR" and not is_valid_gstin(inv.supplier_gstin):
        return ["gstin_invalid"]
    return []


def check_tax_type(inv: Invoice, ref: ReferenceData | None = None) -> list[str]:
    if inv.currency != "INR" or not inv.supplier_gstin or len(inv.supplier_gstin.strip()) < 2:
        return []
    buyer_state = (
        str(ref.buyer.get("state_code", BUYER_STATE_CODE)).strip()
        if ref and ref.buyer
        else str(BUYER_STATE_CODE)
    )
    intra_state = inv.supplier_gstin.strip()[:2] == buyer_state
    if intra_state and _to_dec(inv.igst) > Decimal("0.00"):
        return ["tax_type_mismatch"]
    if not intra_state and (_to_dec(inv.cgst) > Decimal("0.00") or _to_dec(inv.sgst) > Decimal("0.00")):
        return ["tax_type_mismatch"]
    return []


def check_totals(inv: Invoice) -> list[str]:
    if inv.total is None:
        return []
    line_sum = sum((_to_dec(item.amount) for item in inv.line_items), Decimal("0.00"))
    computed = (
        line_sum
        + _to_dec(inv.cgst)
        + _to_dec(inv.sgst)
        + _to_dec(inv.igst)
        + _to_dec(inv.round_off)
    )
    return ["totals_mismatch"] if abs(computed - _to_dec(inv.total)) > Decimal("1.00") else []


def normalize_invoice_number(invoice_number: str | None) -> str:
    """Uppercase with spaces and '/ - # .' removed; leading zeros preserved (AP Policy Section 1)."""
    return re.sub(r"[\s/\-#.]", "", (invoice_number or "").upper())


def financial_year(value: date | str | None) -> str | None:
    """Financial year (1 April to 31 March), e.g. '2026-27' (AP Policy Section 1)."""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        d = value
    else:
        try:
            d = date.fromisoformat(str(value).strip()[:10])
        except ValueError:
            return None
    start = d.year if d.month >= 4 else d.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def _row_supplier_key(gstin: str | None, name: str | None, currency: str | None = None) -> str | None:
    cleaned_gstin = (gstin or "").strip().upper()
    if currency and currency.upper() != "INR":
        return _norm_legal_name(name) or None
    if cleaned_gstin:
        return cleaned_gstin
    return _norm_legal_name(name) or None


def check_duplicate(conn: sqlite3.Connection, ref: ReferenceData, inv: Invoice) -> list[str]:
    if (inv.document_type or "invoice") == "credit_note":
        return []
    inv_key = supplier_key(inv)
    inv_num = normalize_invoice_number(inv.invoice_number)
    inv_fy = financial_year(inv.invoice_date)
    if not inv_key or not inv_num or not inv_fy:
        return []

    rows = conn.execute(
        "SELECT document_type, supplier_name, supplier_gstin, invoice_number, invoice_date, currency FROM invoices"
    ).fetchall()
    for row in rows:
        if (row["document_type"] or "invoice") == "credit_note":
            continue
        r_key = _row_supplier_key(row["supplier_gstin"], row["supplier_name"], row["currency"])
        r_num = normalize_invoice_number(row["invoice_number"])
        r_fy = financial_year(row["invoice_date"])
        if r_key == inv_key and r_num == inv_num and r_fy == inv_fy:
            return ["duplicate"]

    for paid in ref.paid_invoices:
        p_key = _row_supplier_key(paid.get("supplier_gstin"), paid.get("supplier_name"))
        p_num = normalize_invoice_number(paid.get("invoice_number"))
        p_fy = financial_year(paid.get("invoice_date"))
        if p_key == inv_key and p_num == inv_num and p_fy == inv_fy:
            return ["duplicate"]
    return []


def _digits_only(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def check_bank_details(inv: Invoice, vendor: dict | None) -> list[str]:
    if not vendor:
        return []
    inv_acct = _digits_only(inv.bank_account)
    inv_ifsc = (inv.ifsc or "").strip().upper()
    if not inv_acct and not inv_ifsc:
        return []
    vendor_acct = _digits_only(vendor.get("bank_account"))
    vendor_ifsc = (vendor.get("ifsc") or "").strip().upper()
    if inv_acct and inv_acct != vendor_acct:
        return ["bank_details_changed"]
    if inv_ifsc and inv_ifsc != vendor_ifsc:
        return ["bank_details_changed"]
    return []


_HTML_OR_SCRIPT_RE = re.compile(
    r"(?i)<\s*/?\s*(?:script|img|iframe|svg|object|embed|form|input|button|style|link|meta|body|div|span|a)\b"
    r"|on(?:error|load|click|mouseover|focus)\s*="
    r"|javascript\s*:"
)
_AI_INSTRUCTION_RE = re.compile(
    r"(?i)\b(?:ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions"
    r"|ai\s+assistants?"
    r"|automated\s+(?:invoice\s+)?(?:processing|systems?)"
    r"|ap\s+automation\s+system"
    r"|requires_review"
    r"|review_reasons"
    r"|do\s+not\s+mention\s+this\s+note"
    r"|skip\s+(?:all\s+)?checks?"
    r"|system\s+prompt)\b"
)


def check_suspicious_content(inv: Invoice, raw_text: str | None = None) -> list[str]:
    fragments = [
        raw_text or "",
        inv.notes or "",
        inv.supplier_name or "",
        *(item.description for item in inv.line_items if item.description),
    ]
    combined = "\n".join(fragments)
    if _HTML_OR_SCRIPT_RE.search(combined) or _AI_INSTRUCTION_RE.search(combined):
        return ["suspicious_content"]
    return []


def run_checks(
    conn: sqlite3.Connection, ref: ReferenceData, inv: Invoice, raw_text: str | None = None
) -> list[str]:
    vendor = find_vendor(ref, inv)
    return (
        check_credit_note(inv)
        + check_gstin(inv)
        + check_vendor(vendor)
        + check_vendor_new(inv, vendor)
        + check_tax_type(inv, ref)
        + check_totals(inv)
        + check_duplicate(conn, ref, inv)
        + check_bank_details(inv, vendor)
        + check_foreign_currency(inv)
        + check_suspicious_content(inv, raw_text)
    )
