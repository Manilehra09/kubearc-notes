"""Fast tests for Kubearc Notes. They run without a database (in-memory mode)."""
import os

os.environ.pop("DB_HOST", None)

import app as notes  # noqa: E402

client = notes.app.test_client()


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_readyz_without_db():
    r = client.get("/readyz")
    assert r.status_code == 200


def test_add_and_list_note():
    r = client.post("/notes", json={"text": "hello from CI"})
    assert r.status_code == 201
    texts = [n["text"] for n in client.get("/api/notes").get_json()["notes"]]
    assert "hello from CI" in texts


def test_empty_note_rejected():
    r = client.post("/notes", json={"text": "   "})
    assert r.status_code == 400


def test_metrics():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"notes_http_requests_total" in r.data
