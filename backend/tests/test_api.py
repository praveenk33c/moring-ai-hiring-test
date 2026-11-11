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

