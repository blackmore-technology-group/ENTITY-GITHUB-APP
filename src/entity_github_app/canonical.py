from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any, Dict

from . import SCHEMA_ID


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _repo(payload: Dict[str, Any]) -> Dict[str, Any]:
    repo = payload.get("repository") or {}
    owner = repo.get("owner") or {}
    return {
        "full_name": repo.get("full_name"),
        "id": repo.get("id"),
        "owner": owner.get("login"),
        "html_url": repo.get("html_url"),
        "default_branch": repo.get("default_branch"),
    }

def _subject(event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if event == "push":
        head = payload.get("head_commit") or {}
        return {"kind": "git_ref", "ref": payload.get("ref"), "after": payload.get("after"), "head_url": head.get("url")}
    if event == "pull_request":
        pr = payload.get("pull_request") or {}
        return {"kind": "pull_request", "number": pr.get("number"), "state": pr.get("state"), "head_sha": ((pr.get("head") or {}).get("sha")), "base_sha": ((pr.get("base") or {}).get("sha")), "html_url": pr.get("html_url")}
    if event in {"check_run", "check_suite"}:
        obj = payload.get(event) or {}
        return {"kind": event, "id": obj.get("id"), "status": obj.get("status"), "conclusion": obj.get("conclusion"), "head_sha": obj.get("head_sha")}
    if event == "workflow_run":
        run = payload.get("workflow_run") or {}
        return {"kind": "workflow_run", "id": run.get("id"), "name": run.get("name"), "status": run.get("status"), "conclusion": run.get("conclusion"), "head_sha": run.get("head_sha"), "html_url": run.get("html_url")}
    if event == "release":
        rel = payload.get("release") or {}
        return {"kind": "release", "id": rel.get("id"), "tag_name": rel.get("tag_name"), "target_commitish": rel.get("target_commitish"), "draft": rel.get("draft"), "prerelease": rel.get("prerelease"), "html_url": rel.get("html_url")}
    if event == "repository":
        repo = payload.get("repository") or {}
        return {"kind": "repository", "id": repo.get("id"), "full_name": repo.get("full_name"), "visibility": repo.get("visibility")}
    return {"kind": event}

def evidence_candidate(event: str, delivery_id: str, payload: Dict[str, Any], raw_body: bytes) -> Dict[str, Any]:
    installation = payload.get("installation") or {}
    sender = payload.get("sender") or {}
    action = payload.get("action")
    observed_at = utc_now()
    candidate = {
        "schema": SCHEMA_ID,
        "candidate_id": f"github:{delivery_id}",
        "observed_at": observed_at,
        "source": {
            "system": "github",
            "delivery_id": delivery_id,
            "event": event,
            "action": action,
            "repository": _repo(payload),
            "installation_id": installation.get("id"),
            "sender": sender.get("login"),
        },
        "subject": _subject(event, payload),
        "integrity": {"webhook_payload_sha256": sha256_bytes(raw_body)},
        "claim_boundary": {
            "asserts_github_observation_only": True,
            "does_not_assert_legal_ownership": True,
            "does_not_assert_objective_truth": True,
            "does_not_assert_independent_validation": True,
            "does_not_modify_entity_semantics": True,
        },
    }
    candidate["candidate_sha256"] = sha256_bytes(canonical_json(candidate).encode("utf-8"))
    return candidate
