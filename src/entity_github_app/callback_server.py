from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse


class CallbackHandler(BaseHTTPRequestHandler):
    server_version = "ENTITYGitHubCallback/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/github/callback":
            self.send_error(404)
            return
        params = parse_qs(parsed.query)
        state = escape(params.get("state", [""])[0])
        body = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>ENTITY Evidence Bridge</title></head><body>"
            "<h1>ENTITY Evidence Bridge</h1>"
            "<p>GitHub returned successfully to the local callback endpoint.</p>"
            "<p>No user OAuth token is requested or stored by this endpoint.</p>"
            + (f"<p>State received: <code>{state}</code></p>" if state else "")
            + "<p>You can close this tab and return to GitHub.</p></body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def run_callback(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), CallbackHandler)
    print(f"ENTITY GitHub callback listening on http://{host}:{port}/github/callback")
    try:
        server.serve_forever()
    finally:
        server.server_close()
