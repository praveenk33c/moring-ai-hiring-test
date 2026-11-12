"""Process one document end to end: extract -> normalise -> check -> route -> persist."""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from . import db
from .config import get_settings
from .extraction import POLICY_VERSION, PROMPT_VERSION, build_extraction_prompt, extract
from .llm.pricing import cost_usd
from .models import Invoice, LineItem
from .parsing import parse_amount, parse_date
from .reference import ReferenceData
from .validation import run_checks

HIGH_VALUE_THRESHOLD = 500000  # invoices above this need two approvals
_CORE_FIELDS = ("supplier_name", "invoice_number", "invoice_date", "currency", "subtotal", "total")


def _compute_confidence(data: dict, inv: Invoice, review_reasons: list[str]) -> float:
    raw_conf = data.get("confidence")
    if isinstance(raw_conf, (int, float)) and 0.0 <= float(raw_conf) <= 1.0:
        return round(float(raw_conf), 4)
    present = sum(1 for f in _CORE_FIELDS if getattr(inv, f, None) not in (None, ""))
    score = present / len(_CORE_FIELDS)
    if "processing_error" in review_reasons or "totals_mismatch" in review_reasons:
        score *= 0.6
    elif review_reasons:
        score *= 0.85
    return round(score, 4)


def normalize(data: dict) -> Invoice:
    items = [
        LineItem(
            description=str(item.get("description", "")),
            quantity=parse_amount(item.get("quantity")),
            unit_price=parse_amount(item.get("unit_price")),
            amount=parse_amount(item.get("amount")) or 0.0,
        )
        for item in data.get("line_items") or []
    ]
    return Invoice(
        document_type=data.get("document_type") or "invoice",
        supplier_name=data.get("supplier_name"),
        supplier_gstin=data.get("supplier_gstin"),
        invoice_number=data.get("invoice_number"),
        invoice_date=parse_date(data.get("invoice_date")),
        currency=data.get("currency") or "INR",
        subtotal=parse_amount(data.get("subtotal")),
        cgst=parse_amount(data.get("cgst")) or 0.0,
        sgst=parse_amount(data.get("sgst")) or 0.0,
        igst=parse_amount(data.get("igst")) or 0.0,
        round_off=parse_amount(data.get("round_off")) or 0.0,
        total=parse_amount(data.get("total")),
        bank_account=data.get("bank_account"),
        ifsc=data.get("ifsc"),
        po_number=data.get("po_number"),
        notes=data.get("notes"),
        line_items=items,
    )


def process_document(
    conn: sqlite3.Connection,
    ref: ReferenceData,
    raw_text: str,
    document_id: str,
    org_id: str = "meridian",
    filename: str | None = None,
) -> dict:
    data, responses = extract(raw_text, ref)
    inv = normalize(data)
    review_reasons = list(dict.fromkeys(run_checks(conn, ref, inv, raw_text)))
    warnings = list(review_reasons)
    needs_review = len(review_reasons) > 0
    required_approvals = 2 if (inv.total or 0) > HIGH_VALUE_THRESHOLD else 1
    status = "needs_review" if needs_review else "ready_for_approval"

    cur = conn.execute(
        """INSERT INTO invoices (org_id, document_id, filename, raw_text, document_type, supplier_name,
               supplier_gstin, invoice_number, invoice_date, currency, subtotal, cgst, sgst, igst, round_off,
               total, bank_account, ifsc, po_number, notes, line_items_json, warnings_json, needs_review,
               review_reasons_json, required_approvals, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            org_id, document_id, filename, raw_text, inv.document_type, inv.supplier_name, inv.supplier_gstin,
            inv.invoice_number, inv.invoice_date.isoformat() if inv.invoice_date else None, inv.currency,
            inv.subtotal, inv.cgst, inv.sgst, inv.igst, inv.round_off, inv.total, inv.bank_account, inv.ifsc,
            inv.po_number, inv.notes, json.dumps([asdict(i) for i in inv.line_items]), json.dumps(warnings),
            int(needs_review), json.dumps(review_reasons), required_approvals, status,
        ),
    )
    invoice_id = cur.lastrowid
    for r in responses:
        conn.execute(
            "INSERT INTO llm_calls (invoice_id, document_id, model, input_tokens, output_tokens, cost_usd, "
            "latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (invoice_id, document_id, r.model, r.input_tokens, r.output_tokens,
             cost_usd(r.model, r.input_tokens, r.output_tokens), r.latency_ms),
        )

    settings = get_settings()
    model_version = responses[-1].model if responses else settings.llm_model
    decision_snapshot = {
        "status": status,
        "needs_review": needs_review,
        "review_reasons": review_reasons,
        "required_approvals": required_approvals,
    }
    conn.execute(
        """INSERT INTO ai_logs (log_id, invoice_id, document_id, provider, model_version, prompt_version,
               prompt, extraction_result_json, confidence, policy_version, decision_json, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(uuid.uuid4()),
            invoice_id,
            document_id,
            settings.llm_provider,
            model_version,
            PROMPT_VERSION,
            build_extraction_prompt(raw_text, ref),
            json.dumps(data, ensure_ascii=False),
            _compute_confidence(data, inv, review_reasons),
            POLICY_VERSION,
            json.dumps(decision_snapshot, ensure_ascii=False),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    return db.get_invoice(conn, invoice_id)
