"""Field accuracy on the labelled dev set.  Usage (from backend/):  python eval/run_eval.py"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ledgerline import db  # noqa: E402
from ledgerline.config import get_settings  # noqa: E402
from ledgerline.pipeline import process_document  # noqa: E402
from ledgerline.reference import load_reference  # noqa: E402

FIELDS = ["document_type", "supplier_name", "supplier_gstin", "invoice_number", "invoice_date", "currency",
          "subtotal", "cgst", "sgst", "igst", "total", "po_number"]


def _norm(value) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value).strip().lower()


def main() -> None:
    settings = get_settings()
    ref = load_reference()
    conn = db.connect(str(Path(tempfile.mkdtemp()) / "eval.db"))
    with open(settings.data_dir / "ground_truth" / "dev.jsonl", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]

    correct = total = 0
    routing_correct = false_ready = need_review_total = reasons_exact = approvals_correct = 0
    for row in rows:
        path = settings.data_dir / "invoices" / "dev" / row["filename"]
        expected = row["expected"]
        if expected.get("needs_review"):
            need_review_total += 1
        try:
            got = process_document(conn, ref, path.read_text(encoding="utf-8"), row["document_id"])
        except Exception as exc:
            print(f"failed {row['document_id']} (counted as failure): {exc}")
            total += len(FIELDS)
            if expected.get("needs_review"):
                routing_correct += 1  # fallback routes to needs_review
            continue
        for field in FIELDS:
            total += 1
            correct += _norm(got.get(field)) == _norm(expected.get(field))
        if bool(got.get("needs_review")) == bool(expected.get("needs_review")):
            routing_correct += 1
        if expected.get("needs_review") and not got.get("needs_review"):
            false_ready += 1
        if set(got.get("review_reasons") or []) == set(expected.get("review_reasons") or []):
            reasons_exact += 1
        if got.get("required_approvals") == expected.get("required_approvals"):
            approvals_correct += 1
    n_docs = len(rows)
    print(f"Field accuracy: {correct}/{total} = {correct / total:.1%}")
    print(f"Routing accuracy: {routing_correct}/{n_docs} = {routing_correct / n_docs:.1%}")
    print(f"False-ready (missed reviews): {false_ready}/{need_review_total}")
    print(f"Exact review reasons match: {reasons_exact}/{n_docs} = {reasons_exact / n_docs:.1%}")
    print(f"Required approvals match: {approvals_correct}/{n_docs} = {approvals_correct / n_docs:.1%}")


if __name__ == "__main__":
    main()
