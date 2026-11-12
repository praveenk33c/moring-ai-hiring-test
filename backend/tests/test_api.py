import pytest
from fastapi.testclient import TestClient

from ledgerline.api import app


@pytest.fixture
def client(tmp_path, monkeypatch, fake_llm):
    monkeypatch.setenv("LEDGERLINE_DB", str(tmp_path / "api.db"))
    return TestClient(app)


def test_upload_list_get_approve(client):
    uploaded = client.post("/api/invoices", files={"file": ("dev_001.txt", b"some invoice text", "text/plain")})
    assert uploaded.status_code == 200
    invoice_id = uploaded.json()["id"]

    listed = client.get("/api/invoices").json()
    assert [row["id"] for row in listed] == [invoice_id]

    detail = client.get(f"/api/invoices/{invoice_id}").json()
    assert detail["invoice_number"] == "SIS/26-27/0042"

    approved = client.post(f"/api/invoices/{invoice_id}/approve", json={"user_id": "kavya", "note": "ok"})
    assert approved.json()["status"] == "approved"


def test_stats_counts_processed_documents(client):
    client.post("/api/invoices", files={"file": ("a.txt", b"text", "text/plain")})
    assert client.get("/api/stats").json()["invoices_processed"] == 1


def test_approve_is_idempotent_on_double_click(client, tmp_path):
    from ledgerline import db

    uploaded = client.post("/api/invoices", files={"file": ("dev_001.txt", b"some invoice text", "text/plain")})
    invoice_id = uploaded.json()["id"]

    first = client.post(f"/api/invoices/{invoice_id}/approve", json={"user_id": "kavya", "note": "ok"})
    second = client.post(f"/api/invoices/{invoice_id}/approve", json={"user_id": "kavya", "note": "ok"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "approved"
    assert second.json()["status"] == "approved"
    assert second.json()["approvals"] == 1

    conn = db.connect(str(tmp_path / "api.db"))
    try:
        payments = conn.execute("SELECT COUNT(*) FROM payments WHERE invoice_id = ?", (invoice_id,)).fetchone()[0]
        approvals = conn.execute("SELECT COUNT(*) FROM approvals WHERE invoice_id = ?", (invoice_id,)).fetchone()[0]
    finally:
        conn.close()

    assert payments == 1
    assert approvals == 1


def test_two_approval_invoice_requires_distinct_approvers_and_creates_single_payment(client, tmp_path):
    from ledgerline import db

    uploaded = client.post("/api/invoices", files={"file": ("dev_001.txt", b"some invoice text", "text/plain")})
    invoice_id = uploaded.json()["id"]

    conn = db.connect(str(tmp_path / "api.db"))
    conn.execute("UPDATE invoices SET required_approvals = 2 WHERE id = ?", (invoice_id,))
    conn.commit()

    # Same user clicking approve twice must count only once
    r1 = client.post(f"/api/invoices/{invoice_id}/approve", json={"user_id": "kavya", "note": "first"})
    r2 = client.post(f"/api/invoices/{invoice_id}/approve", json={"user_id": "kavya", "note": "retry"})
    assert r1.json()["approvals"] == 1
    assert r2.json()["approvals"] == 1
    assert r2.json()["status"] != "approved"
    assert conn.execute("SELECT COUNT(*) FROM payments WHERE invoice_id = ?", (invoice_id,)).fetchone()[0] == 0

    # Second distinct user completes approval; repeated call creates no extra payment
    r3 = client.post(f"/api/invoices/{invoice_id}/approve", json={"user_id": "sunil", "note": "second"})
    r4 = client.post(f"/api/invoices/{invoice_id}/approve", json={"user_id": "sunil", "note": "double-click"})
    assert r3.json()["approvals"] == 2
    assert r3.json()["status"] == "approved"
    assert r4.json()["approvals"] == 2
    assert r4.json()["status"] == "approved"

    payments = conn.execute("SELECT COUNT(*) FROM payments WHERE invoice_id = ?", (invoice_id,)).fetchone()[0]
    conn.close()
    assert payments == 1


def test_pricing_usd_per_mtok_and_stats_cost(client, monkeypatch):
    from ledgerline.llm.fake import FakeClient
    from ledgerline.llm.pricing import cost_usd

    # 1M input + 1M output on claude-opus-5-5 should be $4.00 + $20.00 = $24.00 (not $0.024)
    assert cost_usd("claude-opus-5-5", 1_000_000, 1_000_000) == pytest.approx(24.0)
    assert cost_usd("claude-sonnet-5-5", 1_000_000, 1_000_000) == pytest.approx(12.0)
    assert cost_usd("gpt-4o-mini", 1_000_000, 1_000_000) == pytest.approx(0.75)

    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: FakeClient(model="claude-opus-5-5"))
    uploaded = client.post("/api/invoices", files={"file": ("a.txt", b"text", "text/plain")}).json()
    stats = client.get("/api/stats").json()
    expected_usd = cost_usd(
        "claude-opus-5-5",
        uploaded["usage"]["input_tokens"],
        uploaded["usage"]["output_tokens"],
    )
    assert stats["llm_cost_inr"] == pytest.approx(round(expected_usd * 88.0, 2))
    assert stats["llm_cost_inr"] > 0.2  # Previously 1000x too small (0.00 INR when rounded)


def test_server_side_approval_enforcement_and_audit_log(client, monkeypatch):
    import json
    from ledgerline.llm.fake import CANNED_EXTRACTION, FakeClient

    # 1. Credit note cannot be approved for payment (Policy 4.1)
    cn_payload = dict(CANNED_EXTRACTION, document_type="credit_note")
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: FakeClient([json.dumps(cn_payload)]))
    cn_inv = client.post("/api/invoices", files={"file": ("cn.txt", b"credit note", "text/plain")}).json()
    res_cn = client.post(f"/api/invoices/{cn_inv['id']}/approve", json={"user_id": "kavya", "note": "try approve"})
    assert res_cn.status_code == 400

    # 2. Duplicate invoice cannot be approved, but can be rejected and is logged in audit_log (Policy 4.4 & 4.7)
    dup_payload = dict(CANNED_EXTRACTION, invoice_number="SIS/26-27/0018", invoice_date="2026-04-02")
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: FakeClient([json.dumps(dup_payload)]))
    dup_inv = client.post("/api/invoices", files={"file": ("dup.txt", b"duplicate invoice", "text/plain")}).json()
    assert "duplicate" in dup_inv["review_reasons"]
    res_dup = client.post(f"/api/invoices/{dup_inv['id']}/approve", json={"user_id": "kavya", "note": "override"})
    assert res_dup.status_code == 400

    rej_dup = client.post(
        f"/api/invoices/{dup_inv['id']}/reject",
        json={"user_id": "kavya", "note": "Confirmed duplicate of paid invoice"},
    )
    assert rej_dup.status_code == 200
    assert rej_dup.json()["status"] == "rejected"

    # Rejected invoice cannot subsequently be approved
    res_after_rej = client.post(
        f"/api/invoices/{dup_inv['id']}/approve", json={"user_id": "sunil", "note": "try after reject"}
    )
    assert res_after_rej.status_code == 400

    dup_detail = client.get(f"/api/invoices/{dup_inv['id']}").json()
    assert len(dup_detail["audit_log"]) == 1
    assert dup_detail["audit_log"][0]["action"] == "reject"
    assert dup_detail["audit_log"][0]["user_id"] == "kavya"
    assert dup_detail["audit_log"][0]["document_id"] == "dup"
    assert dup_detail["audit_log"][0]["note"] == "Confirmed duplicate of paid invoice"
    assert dup_detail["audit_log"][0]["created_at"]

    # 3. Document with needs_review=True requires a non-empty note on approval (Policy 4.5 & 4.7)
    rev_payload = dict(CANNED_EXTRACTION, ifsc="HDFC0009999")  # triggers bank_details_changed
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: FakeClient([json.dumps(rev_payload)]))
    rev_inv = client.post("/api/invoices", files={"file": ("rev.txt", b"review invoice", "text/plain")}).json()
    assert rev_inv["needs_review"] is True

    res_no_note = client.post(f"/api/invoices/{rev_inv['id']}/approve", json={"user_id": "kavya", "note": "   "})
    assert res_no_note.status_code == 400

    res_with_note = client.post(
        f"/api/invoices/{rev_inv['id']}/approve",
        json={"user_id": "kavya", "note": "Verified new IFSC with vendor treasury"},
    )
    assert res_with_note.status_code == 200
    assert res_with_note.json()["status"] == "approved"

    rev_detail = client.get(f"/api/invoices/{rev_inv['id']}").json()
    assert len(rev_detail["audit_log"]) == 1
    assert rev_detail["audit_log"][0]["action"] == "approve"
    assert rev_detail["audit_log"][0]["user_id"] == "kavya"
    assert rev_detail["audit_log"][0]["document_id"] == "rev"
    assert rev_detail["audit_log"][0]["note"] == "Verified new IFSC with vendor treasury"




