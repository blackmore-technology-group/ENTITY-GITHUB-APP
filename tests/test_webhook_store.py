import json
import tempfile
import unittest
from pathlib import Path

from entity_github_app.canonical import evidence_candidate
from entity_github_app.store import EvidenceStore
from entity_github_app.webhook import expected_signature, verify_signature


class WebhookStoreTests(unittest.TestCase):
    def test_signature(self):
        body = b'{"zen":"test"}'
        sig = expected_signature("secret", body)
        self.assertTrue(verify_signature("secret", body, sig))
        self.assertFalse(verify_signature("wrong", body, sig))

    def test_dedup_and_audit_chain(self):
        payload = {"ref": "refs/heads/main", "after": "a" * 40, "repository": {"full_name": "btg/example", "owner": {"login": "btg"}}}
        body = json.dumps(payload).encode()
        candidate = evidence_candidate("push", "d-1", payload, body)
        with tempfile.TemporaryDirectory() as temp:
            store = EvidenceStore(Path(temp) / "test.sqlite")
            try:
                self.assertTrue(store.record("push", "d-1", candidate))
                self.assertFalse(store.record("push", "d-1", candidate))
                self.assertEqual(store.counts()["candidates"], 1)
                self.assertTrue(store.verify_audit()["ok"])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
