from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict

from .canonical import canonical_json, sha256_bytes, utc_now

SCHEMA = """
CREATE TABLE IF NOT EXISTS deliveries(
  delivery_id TEXT PRIMARY KEY, event TEXT NOT NULL, received_at TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL, candidate_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS candidates(
  candidate_id TEXT PRIMARY KEY, delivery_id TEXT NOT NULL UNIQUE,
  event TEXT NOT NULL, repository TEXT, candidate_json TEXT NOT NULL,
  candidate_sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit(
  seq INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
  action TEXT NOT NULL, object_id TEXT NOT NULL, payload_json TEXT NOT NULL,
  prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL
);
"""


class EvidenceStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        self.db.close()

    def _audit(self, action: str, object_id: str, payload: Dict[str, Any]) -> None:
        row = self.db.execute("SELECT event_hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        prev = row[0] if row else "0" * 64
        event = {
            "timestamp": utc_now(),
            "action": action,
            "object_id": object_id,
            "payload": payload,
            "prev_hash": prev,
        }
        event_hash = sha256_bytes(canonical_json(event).encode("utf-8"))
        self.db.execute(
            "INSERT INTO audit(timestamp,action,object_id,payload_json,prev_hash,event_hash) VALUES(?,?,?,?,?,?)",
            (event["timestamp"], action, object_id, canonical_json(payload), prev, event_hash),
        )

    def record(self, event: str, delivery_id: str, candidate: Dict[str, Any]) -> bool:
        if self.db.execute("SELECT 1 FROM deliveries WHERE delivery_id=?", (delivery_id,)).fetchone():
            return False
        repo = ((candidate.get("source") or {}).get("repository") or {}).get("full_name")
        payload_hash = (candidate.get("integrity") or {}).get("webhook_payload_sha256")
        candidate_hash = candidate.get("candidate_sha256")
        recorded_at = utc_now()
        with self.db:
            self.db.execute(
                "INSERT INTO deliveries(delivery_id,event,received_at,payload_sha256,candidate_sha256) VALUES(?,?,?,?,?)",
                (delivery_id, event, recorded_at, payload_hash, candidate_hash),
            )
            self.db.execute(
                "INSERT INTO candidates(candidate_id,delivery_id,event,repository,candidate_json,candidate_sha256,recorded_at) VALUES(?,?,?,?,?,?,?)",
                (candidate["candidate_id"], delivery_id, event, repo, canonical_json(candidate), candidate_hash, recorded_at),
            )
            self._audit("CANDIDATE_RECORDED", candidate["candidate_id"], {"delivery_id": delivery_id, "event": event, "repository": repo, "candidate_sha256": candidate_hash})
        return True

    def get_candidate(self, candidate_id: str) -> Dict[str, Any] | None:
        row = self.db.execute("SELECT candidate_json FROM candidates WHERE candidate_id=?", (candidate_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def counts(self) -> Dict[str, int]:
        return {
            "deliveries": self.db.execute("SELECT count(*) FROM deliveries").fetchone()[0],
            "candidates": self.db.execute("SELECT count(*) FROM candidates").fetchone()[0],
            "audit_events": self.db.execute("SELECT count(*) FROM audit").fetchone()[0],
        }

    def verify_audit(self) -> Dict[str, Any]:
        prev = "0" * 64
        errors = []
        count = 0
        for row in self.db.execute("SELECT * FROM audit ORDER BY seq"):
            payload = json.loads(row["payload_json"])
            event = {
                "timestamp": row["timestamp"],
                "action": row["action"],
                "object_id": row["object_id"],
                "payload": payload,
                "prev_hash": row["prev_hash"],
            }
            expected = sha256_bytes(canonical_json(event).encode("utf-8"))
            if row["prev_hash"] != prev or row["event_hash"] != expected:
                errors.append(row["seq"])
            prev = row["event_hash"]
            count += 1
        return {
            "ok": not errors,
            "events": count,
            "last_hash": prev,
            "errors": errors,
            "boundary": "Local hash chain; external/WORM preservation is a separate control.",
        }
