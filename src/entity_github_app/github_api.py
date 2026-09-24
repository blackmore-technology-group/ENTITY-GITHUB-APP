from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict

from .canonical import canonical_json

API = "https://api.github.com"
DEFAULT_OPENSSL = Path(r"E:\ENTITY_ACTIVE\TOOLS\PortableGit\usr\bin\openssl.exe")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _openssl_path() -> Path:
    configured = os.environ.get("ENTITY_GITHUB_OPENSSL")
    path = Path(configured) if configured else DEFAULT_OPENSSL
    if not path.is_file():
        raise RuntimeError(f"OpenSSL not found: {path}")
    return path


def create_app_jwt(app_id: str, private_key_path: str | Path, lifetime_seconds: int = 540) -> str:
    now = int(time.time())
    header = _b64url(canonical_json({"alg": "RS256", "typ": "JWT"}).encode("utf-8"))
    payload = _b64url(canonical_json({"iat": now - 60, "exp": now + lifetime_seconds, "iss": str(app_id)}).encode("utf-8"))
    signing_input = f"{header}.{payload}".encode("ascii")
    key = Path(private_key_path)
    if not key.is_file():
        raise RuntimeError(f"GitHub App private key not found: {key}")
    proc = subprocess.run(
        [str(_openssl_path()), "dgst", "-sha256", "-sign", str(key)],
        input=signing_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace").strip())
    return f"{header}.{payload}.{_b64url(proc.stdout)}"


def api_request(method: str, path: str, token: str, body: Dict[str, Any] | None = None) -> Dict[str, Any]:
    data = canonical_json(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "entity-github-app/0.1")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code}: {detail}") from exc


def installation_token(app_id: str, private_key_path: str | Path, installation_id: int) -> str:
    jwt = create_app_jwt(app_id, private_key_path)
    result = api_request("POST", f"/app/installations/{installation_id}/access_tokens", jwt, {})
    token = result.get("token")
    if not token:
        raise RuntimeError("GitHub did not return an installation token")
    return token


def repository_snapshot(token: str, full_name: str) -> Dict[str, Any]:
    repo = api_request("GET", f"/repos/{full_name}", token)
    return {
        "id": repo.get("id"),
        "full_name": repo.get("full_name"),
        "default_branch": repo.get("default_branch"),
        "visibility": repo.get("visibility"),
        "archived": repo.get("archived"),
        "disabled": repo.get("disabled"),
        "pushed_at": repo.get("pushed_at"),
        "updated_at": repo.get("updated_at"),
    }
