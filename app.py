"""Kubearc Notes: a tiny Flask app for the Kubernetes for DevOps course.

Settings come from environment variables. Without DB_HOST it keeps notes in memory,
so it runs anywhere (docker run, tests). With DB_HOST it uses Postgres.
"""
import os
import socket
import threading
import time

from flask import Flask, Response, jsonify, render_template_string, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

APP_ENV = os.getenv("APP_ENV", "dev")
APP_TITLE = os.getenv("APP_TITLE", "Kubearc Notes")
APP_VERSION = os.getenv("APP_VERSION", "dev")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME", "notes")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
POD = socket.gethostname()

app = Flask(__name__)

REQUESTS = Counter("notes_http_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("notes_http_request_seconds", "Request duration in seconds", ["path"])
CREATED = Counter("notes_created_total", "Notes created")

_memory = []
_lock = threading.Lock()


def db():
    import psycopg
    return psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER,
                           password=DB_PASSWORD, connect_timeout=3)


def init_db():
    """Wait for Postgres, then create the table. The startup probe gives us about 60 s."""
    if not DB_HOST:
        return
    for _ in range(30):
        try:
            with db() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS notes ("
                             "id serial PRIMARY KEY, text text NOT NULL, "
                             "created timestamptz DEFAULT now())")
            print("database ready", flush=True)
            return
        except Exception as exc:  # noqa: BLE001
            print(f"waiting for database {DB_HOST}: {exc}", flush=True)
            time.sleep(2)


def list_notes():
    if not DB_HOST:
        with _lock:
            return list(reversed(_memory))
    with db() as conn:
        rows = conn.execute("SELECT id, text, created FROM notes ORDER BY id DESC LIMIT 50").fetchall()
    return [{"id": r[0], "text": r[1], "created": r[2].isoformat()} for r in rows]


def add_note(text):
    if not DB_HOST:
        with _lock:
            _memory.append({"id": len(_memory) + 1, "text": text,
                            "created": time.strftime("%Y-%m-%dT%H:%M:%S")})
        return
    with db() as conn:
        conn.execute("INSERT INTO notes(text) VALUES (%s)", (text,))


@app.before_request
def _start():
    request._t0 = time.perf_counter()


@app.after_request
def _record(resp):
    if request.path != "/metrics":
        REQUESTS.labels(request.method, request.path, str(resp.status_code)).inc()
        LATENCY.labels(request.path).observe(time.perf_counter() - request._t0)
    return resp


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>{{ title }}</title>
<style>body{font-family:sans-serif;max-width:720px;margin:40px auto;background:#f6f5f0;color:#14213d}
.tag{background:#2f5fc4;color:#fff;padding:2px 8px;border-radius:6px;font-size:13px}
li{margin:6px 0}</style></head><body>
<h1>{{ title }}</h1>
<p><span class="tag">env: {{ env }}</span> <span class="tag">version: {{ version }}</span>
<span class="tag">pod: {{ pod }}</span></p>
<form method="post" action="/notes"><input name="text" size="50" placeholder="Write a note">
<button>Add</button></form>
<ul>{% for n in notes %}<li>{{ n.text }}</li>{% endfor %}</ul>
</body></html>"""


@app.get("/")
def index():
    return render_template_string(PAGE, title=APP_TITLE, env=APP_ENV, version=APP_VERSION,
                                  pod=POD, notes=list_notes())


@app.get("/api/notes")
def api_notes():
    return jsonify(env=APP_ENV, version=APP_VERSION, pod=POD, notes=list_notes())


@app.post("/notes")
def create_note():
    data = request.get_json(silent=True) or request.form
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify(error="text is required"), 400
    add_note(text[:500])
    CREATED.inc()
    if request.is_json:
        return jsonify(status="created"), 201
    return "", 303, {"Location": "/"}


@app.get("/healthz")
def healthz():
    # Liveness: only the process itself. Never the database.
    return jsonify(status="ok")


@app.get("/readyz")
def readyz():
    # Readiness: can we serve real requests? Checks the database when there is one.
    if DB_HOST:
        try:
            with db() as conn:
                conn.execute("SELECT 1")
        except Exception as exc:  # noqa: BLE001
            return jsonify(status="not ready", error=str(exc)), 503
    return jsonify(status="ready")


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
