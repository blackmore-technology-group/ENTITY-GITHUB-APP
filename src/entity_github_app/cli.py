from __future__ import annotations

import argparse
import json

from .callback_server import run_callback
from .github_api import create_app_jwt, installation_token, repository_snapshot
from .server import run
from .store import EvidenceStore


def _print(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="entity-github-app")
    sp = p.add_subparsers(dest="command", required=True)
    serve = sp.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)
    serve.add_argument("--db", default="entity_github_app.sqlite")
    callback = sp.add_parser("callback")
    callback.add_argument("--host", default="127.0.0.1")
    callback.add_argument("--port", type=int, default=8765)
    status = sp.add_parser("status")
    status.add_argument("--db", default="entity_github_app.sqlite")
    verify = sp.add_parser("verify")
    verify.add_argument("--db", default="entity_github_app.sqlite")
    jwt = sp.add_parser("jwt")
    jwt.add_argument("--app-id", required=True)
    jwt.add_argument("--private-key", required=True)
    snap = sp.add_parser("snapshot")
    snap.add_argument("--app-id", required=True)
    snap.add_argument("--private-key", required=True)
    snap.add_argument("--installation-id", required=True, type=int)
    snap.add_argument("--repository", required=True)
    return p


def main() -> None:
    a = build_parser().parse_args()
    if a.command == "serve":
        run(a.host, a.port, a.db)
        return
    if a.command == "callback":
        run_callback(a.host, a.port)
        return
    if a.command in {"status", "verify"}:
        store = EvidenceStore(a.db)
        try:
            _print(store.counts() if a.command == "status" else store.verify_audit())
        finally:
            store.close()
        return
    if a.command == "jwt":
        token = create_app_jwt(a.app_id, a.private_key)
        _print({"jwt_created": True, "segments": len(token.split(".")), "token_not_printed": True})
        return
    token = installation_token(a.app_id, a.private_key, a.installation_id)
    _print(repository_snapshot(token, a.repository))


if __name__ == "__main__":
    main()
