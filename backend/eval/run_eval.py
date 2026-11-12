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
    routing_correct = false_ready = false_review = need_review_total = clean_total = reasons_exact = approvals_correct = 0
    latencies_ms: list[int] = []
    costs_inr: list[float] = []
    n_docs = len(rows)

    for idx, row in enumerate(rows, 1):
        path = settings.data_dir / "invoices" / "dev" / row["filename"]
        expected = row["expected"]
        if expected.get("needs_review"):
            need_review_total += 1
        else:
            clean_total += 1
        try:
            got = process_document(conn, ref, path.read_text(encoding="utf-8"), row["document_id"])
        except Exception as exc:
            print(f"[{idx}/{n_docs}] {row['document_id']} FAILED (counted as failure): {exc}", flush=True)
            total += len(FIELDS)
            if expected.get("needs_review"):
                routing_correct += 1  # fallback routes to needs_review
            else:
                false_review += 1
            continue

        doc_correct = 0
        for field in FIELDS:
            total += 1
            matched = _norm(got.get(field)) == _norm(expected.get(field))
            correct += matched
            doc_correct += matched

        route_ok = bool(got.get("needs_review")) == bool(expected.get("needs_review"))
        if route_ok:
            routing_correct += 1
        if expected.get("needs_review") and not got.get("needs_review"):
            false_ready += 1
        if not expected.get("needs_review") and got.get("needs_review"):
            false_review += 1

        reasons_ok = set(got.get("review_reasons") or []) == set(expected.get("review_reasons") or [])
        if reasons_ok:
            reasons_exact += 1
        if got.get("required_approvals") == expected.get("required_approvals"):
            approvals_correct += 1

        usage = got.get("usage") or {}
        lat = int(usage.get("latency_ms") or 0)
        cost = float(usage.get("cost_inr") or 0.0)
        latencies_ms.append(lat)
        costs_inr.append(cost)
        print(
            f"[{idx:02d}/{n_docs}] {row['document_id']} | fields={doc_correct}/{len(FIELDS)} "
            f"| route={'OK' if route_ok else 'MISMATCH'} | reasons={'OK' if reasons_ok else got.get('review_reasons')} "
            f"| {lat}ms | ₹{cost:.4f}",
            flush=True,
        )

    lat_sorted = sorted(latencies_ms) if latencies_ms else [0]
    p50_ms = lat_sorted[len(lat_sorted) // 2]
    p95_ms = lat_sorted[min(len(lat_sorted) - 1, int(len(lat_sorted) * 0.95))]
    avg_cost = sum(costs_inr) / n_docs if n_docs else 0.0

    print("-" * 72, flush=True)
    print(f"Field accuracy:             {correct}/{total} = {correct / total:.1%}")
    print(f"Routing accuracy:           {routing_correct}/{n_docs} = {routing_correct / n_docs:.1%}")
    print(f"False-ready (missed review):{false_ready}/{need_review_total}")
    print(f"False-review (over-flagged):{false_review}/{clean_total}")
    print(f"Exact review reasons match: {reasons_exact}/{n_docs} = {reasons_exact / n_docs:.1%}")
    print(f"Required approvals match:   {approvals_correct}/{n_docs} = {approvals_correct / n_docs:.1%}")
    print(f"Latency (p50 / p95):        {p50_ms} ms / {p95_ms} ms")
    print(f"Avg LLM cost / document:    ₹{avg_cost:.4f} (total ₹{sum(costs_inr):.4f})", flush=True)


if __name__ == "__main__":
    main()
