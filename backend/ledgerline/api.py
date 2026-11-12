"""HTTP API used by the reviewer UI.  Run: uvicorn ledgerline.api:app --reload"""
from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import db
from .config import USD_TO_INR, get_settings
from .pipeline import process_document
from .reference import load_reference

app = FastAPI(title="Ledgerline API", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def get_conn():
    conn = db.connect(get_settings().db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_org(x_org_id: str = Header(default="meridian")) -> str:
    return x_org_id


class DecisionRequest(BaseModel):
    user_id: str
    note: str = ""


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/invoices")
async def upload_invoice(file: UploadFile, org_id: str = Depends(get_org), conn=Depends(get_conn)):
    raw_text = (await file.read()).decode("utf-8")
    document_id = (file.filename or "upload").rsplit(".", 1)[0]
    return process_document(conn, load_reference(), raw_text, document_id, org_id=org_id, filename=file.filename)


@app.get("/api/invoices")
def list_invoices(org_id: str = Depends(get_org), conn=Depends(get_conn)):
    rows = conn.execute(
        "SELECT id, document_id, supplier_name, invoice_number, invoice_date, currency, total, status, "
        "needs_review FROM invoices WHERE org_id = ? ORDER BY id DESC",
        (org_id,),
    ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/invoices/{invoice_id}")
def get_invoice(invoice_id: int, conn=Depends(get_conn)):
    invoice = db.get_invoice(conn, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@app.post("/api/invoices/{invoice_id}/approve")
def approve_invoice(invoice_id: int, body: DecisionRequest, conn=Depends(get_conn)):
    invoice = db.get_invoice(conn, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.get("document_type") == "credit_note" or invoice.get("required_approvals", 1) == 0:
        raise HTTPException(status_code=400, detail="Credit notes cannot be approved for payment")

    if "duplicate" in (invoice.get("review_reasons") or []):
        raise HTTPException(status_code=400, detail="Invoices flagged as duplicate cannot be approved")

    if invoice["status"] == "rejected":
        raise HTTPException(status_code=400, detail="Rejected invoices cannot be approved")

    if invoice["status"] == "approved":
        approvals = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM approvals WHERE invoice_id = ?", (invoice_id,)
        ).fetchone()[0]
        return {
            "id": invoice_id,
            "approvals": approvals,
            "required_approvals": invoice["required_approvals"],
            "status": "approved",
        }

    if invoice["needs_review"] and not (body.note or "").strip():
        raise HTTPException(
            status_code=400,
            detail="An approver must record a note when approving a document that needed review",
        )

    cur_app = conn.execute(
        "INSERT OR IGNORE INTO approvals (invoice_id, user_id, note) VALUES (?, ?, ?)",
        (invoice_id, body.user_id, body.note),
    )
    if cur_app.rowcount == 1:
        conn.execute(
            "INSERT INTO audit_log (invoice_id, document_id, action, user_id, note) VALUES (?, ?, 'approve', ?, ?)",
            (invoice_id, invoice["document_id"], body.user_id, body.note),
        )
    approvals = conn.execute(
        "SELECT COUNT(DISTINCT user_id) FROM approvals WHERE invoice_id = ?", (invoice_id,)
    ).fetchone()[0]
    status = invoice["status"]
    if invoice["required_approvals"] > 0 and approvals >= invoice["required_approvals"]:
        status = "approved"
        cur = conn.execute(
            "UPDATE invoices SET status = 'approved' WHERE id = ? AND status != 'approved'",
            (invoice_id,),
        )
        if cur.rowcount == 1:
            conn.execute(
                "INSERT OR IGNORE INTO payments (invoice_id, amount) VALUES (?, ?)",
                (invoice_id, invoice["total"]),
            )
    conn.commit()
    return {
        "id": invoice_id,
        "approvals": approvals,
        "required_approvals": invoice["required_approvals"],
        "status": status,
    }


@app.post("/api/invoices/{invoice_id}/reject")
def reject_invoice(invoice_id: int, body: DecisionRequest, conn=Depends(get_conn)):
    invoice = db.get_invoice(conn, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice["status"] == "approved":
        raise HTTPException(status_code=400, detail="Approved invoices cannot be rejected")
    if invoice["status"] != "rejected":
        conn.execute("UPDATE invoices SET status = 'rejected' WHERE id = ?", (invoice_id,))
        conn.execute(
            "INSERT INTO audit_log (invoice_id, document_id, action, user_id, note) VALUES (?, ?, 'reject', ?, ?)",
            (invoice_id, invoice["document_id"], body.user_id, body.note),
        )
        conn.commit()
    return {"id": invoice_id, "status": "rejected"}


@app.get("/api/stats")
def stats(org_id: str = Depends(get_org), conn=Depends(get_conn)):
    """Feeds the cost dashboard."""
    row = conn.execute(
        "SELECT COUNT(DISTINCT c.invoice_id) AS invoices, COALESCE(SUM(c.cost_usd), 0) AS cost_usd "
        "FROM llm_calls c JOIN invoices i ON i.id = c.invoice_id WHERE i.org_id = ?",
        (org_id,),
    ).fetchone()
    total_inr = row["cost_usd"] * USD_TO_INR
    return {
        "invoices_processed": row["invoices"],
        "llm_cost_inr": round(total_inr, 2),
        "avg_llm_cost_per_invoice_inr": round(total_inr / row["invoices"], 4) if row["invoices"] else 0.0,
    }
