from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

from .canonical import evidence_candidate
from .store import EvidenceStore
from .webhook import verify_signature

MAX_BODY = 5 * 1024 * 1024
SUPPORTED = {"push", "pull_request", "check_run", "check_suite", "workflow_run", "release", "repository", "installation"}


class AppServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], secret: str, db_path: str | Path):
        super().__init__(address, Handler)
        self.webhook_secret = secret
        self.db_path = str(db_path)


class Handler(BaseHTTPRequestHandler):
    server_version = "ENTITYGitHubApp/0.1"

    def _json(self, status: int, value: Dict[str, Any]) -> None:
        data = json.dumps(value, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path != "/health":
            self._json(404, {"ok": False, "error": "not_found"})
            return
        store = EvidenceStore(self.server.db_path)
        try:
            self._json(200, {"ok": True, "service": "entity-github-app", "store": store.counts(), "audit": store.verify_audit()})
        finally:
            store.close()

    def do_POST(self) -> None:
        if self.path != "/webhook":
            self._json(404, {"ok": False, "error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"ok": False, "error": "invalid_content_length"})
            return
        if length <= 0 or length > MAX_BODY:
            self._json(413, {"ok": False, "error": "invalid_body_size"})
            return
        body = self.rfile.read(length)
        signature = self.headers.get("X-Hub-Signature-256")
        if not verify_signature(self.server.webhook_secret, body, signature):
            self._json(401, {"ok": False, "error": "invalid_signature"})
            return
        event = self.headers.get("X-GitHub-Event") or ""
        delivery = self.headers.get("X-GitHub-Delivery") or ""
        if not delivery:
            self._json(400, {"ok": False, "error": "missing_delivery_id"})
            return
        if event == "ping":
            self._json(200, {"ok": True, "message": "pong", "delivery_id": delivery})
            return
        if event not in SUPPORTED:
            self._json(202, {"ok": True, "ignored": True, "event": event})
            return
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "invalid_json"})
            return
        candidate = evidence_candidate(event, delivery, payload, body)
        store = EvidenceStore(self.server.db_path)
        try:
            created = store.record(event, delivery, candidate)
            self._json(201 if created else 200, {"ok": True, "created": created, "candidate_id": candidate["candidate_id"], "candidate_sha256": candidate["candidate_sha256"]})
        finally:
            store.close()

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def run(host: str = "127.0.0.1", port: int = 8787, db_path: str | Path = "entity_github_app.sqlite") -> None:
    secret = os.environ.get("ENTITY_GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        raise RuntimeError("ENTITY_GITHUB_WEBHOOK_SECRET is required")
    server = AppServer((host, port), secret, db_path)
    print(f"ENTITY GitHub App listening on http://{host}:{port}")
    try:
        server.serve_forever()
    finally:
        server.server_close()
