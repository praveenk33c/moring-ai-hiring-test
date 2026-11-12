"""Batch processing.  This is the interface Meridian's nightly batch job uses:

    python -m ledgerline.cli predict --input ../data/invoices/dev --reference ../data/reference \
        --output ../submission/predictions_dev.jsonl

See docs/OUTPUT_CONTRACT.md for the output format.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import db
from .pipeline import process_document
from .reference import load_reference

SUPPORTED_SUFFIXES = {".txt", ".eml", ".json"}
MONEY_FIELDS = ["subtotal", "cgst", "sgst", "igst", "round_off", "total"]
ZERO_DEFAULT_MONEY_FIELDS = {"cgst", "sgst", "igst", "round_off"}
TEXT_FIELDS = ["document_type", "supplier_name", "supplier_gstin", "invoice_number", "invoice_date", "currency",
               "bank_account", "ifsc", "po_number"]
NULLABLE_TEXT_FIELDS = {"supplier_gstin", "bank_account", "ifsc", "po_number"}


def _fmt_money(value: float | str | None, default_zero: bool = False) -> str | None:
    if value is None or value == "":
        return "0.00" if default_zero else None
    num = float(value)
    if abs(num) < 1e-9:
        num = 0.0
    return f"{num:.2f}"


def _fmt_qty(value: float | str | None) -> str | None:
    if value is None or value == "":
        return None
    num = float(value)
    if num.is_integer():
        return str(int(round(num)))
    return f"{num:.2f}".rstrip("0").rstrip(".")


def _fmt_line_item(item: dict) -> dict:
    return {
        "description": str(item.get("description") or ""),
        "quantity": _fmt_qty(item.get("quantity")),
        "unit_price": _fmt_money(item.get("unit_price")),
        "amount": _fmt_money(item.get("amount"), default_zero=True),
    }


def to_contract(invoice: dict) -> dict:
    out: dict = {"document_id": invoice["document_id"]}
    for f in TEXT_FIELDS:
        val = invoice.get(f)
        if f in NULLABLE_TEXT_FIELDS and (val is None or str(val).strip() == ""):
            out[f] = None
        else:
            out[f] = val
    for f in MONEY_FIELDS:
        out[f] = _fmt_money(invoice.get(f), default_zero=(f in ZERO_DEFAULT_MONEY_FIELDS))
    out["line_items"] = [_fmt_line_item(item) for item in (invoice.get("line_items") or [])]
    out["needs_review"] = bool(invoice["needs_review"])
    out["review_reasons"] = list(invoice["review_reasons"])
    out["required_approvals"] = int(invoice["required_approvals"])
    out["usage"] = invoice["usage"]
    return out


def _fallback_contract(document_id: str) -> dict:
    out: dict = {"document_id": document_id, "document_type": "invoice"}
    for f in TEXT_FIELDS:
        if f != "document_type":
            out[f] = "INR" if f == "currency" else None
    for f in MONEY_FIELDS:
        out[f] = None if f in ("subtotal", "total") else "0.00"
    out["line_items"] = []
    out["needs_review"] = True
    out["review_reasons"] = ["processing_error"]
    out["required_approvals"] = 1
    out["usage"] = {"llm_calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_inr": 0.0, "latency_ms": 0}
    return out


def predict(args: argparse.Namespace) -> None:
    ref = load_reference(args.reference)
    db_path = args.db or str(Path(tempfile.mkdtemp(prefix="ledgerline-")) / "predict.db")
    conn = db.connect(db_path)
    documents = sorted(p for p in Path(args.input).iterdir() if p.suffix in SUPPORTED_SUFFIXES)
    written = 0
    with open(args.output, "w", encoding="utf-8") as out:
        for path in documents:
            try:
                invoice = process_document(conn, ref, path.read_text(encoding="utf-8"), path.stem,
                                           filename=path.name)
                record = to_contract(invoice)
            except Exception as exc:  # never skip a document per OUTPUT_CONTRACT.md
                print(f"[processing_error] {path.name}: {exc}", file=sys.stderr)
                record = _fallback_contract(path.stem)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
    print(f"wrote {written}/{len(documents)} predictions to {args.output}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ledgerline")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("predict", help="process a folder of documents and write predictions.jsonl")
    p.add_argument("--input", required=True, help="folder containing .txt / .eml / .json documents")
    p.add_argument("--reference", default=None, help="folder with vendors.csv, paid_invoices.csv, buyer.json")
    p.add_argument("--output", required=True, help="where to write predictions (JSON Lines)")
    p.add_argument("--db", default=None, help="SQLite file to use (default: a fresh temporary database)")
    args = parser.parse_args(argv)
    if args.command == "predict":
        predict(args)


if __name__ == "__main__":
    main()
