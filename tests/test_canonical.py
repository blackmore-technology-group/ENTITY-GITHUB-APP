import json
import unittest

from entity_github_app.canonical import evidence_candidate


class CanonicalTests(unittest.TestCase):
    def test_pull_request_candidate_preserves_claim_boundary(self):
        payload = {
            "action": "opened",
            "repository": {"id": 7, "full_name": "btg/example", "owner": {"login": "btg"}, "default_branch": "main"},
            "pull_request": {"number": 4, "state": "open", "head": {"sha": "abc"}, "base": {"sha": "def"}, "html_url": "https://example/pr/4"},
            "installation": {"id": 99},
            "sender": {"login": "developer"},
        }
        raw = json.dumps(payload, sort_keys=True).encode()
        result = evidence_candidate("pull_request", "delivery-1", payload, raw)
        self.assertEqual(result["schema"], "entity.github.evidence-candidate.v1")
        self.assertEqual(result["subject"]["head_sha"], "abc")
        self.assertTrue(result["claim_boundary"]["does_not_modify_entity_semantics"])
        self.assertTrue(result["claim_boundary"]["does_not_assert_independent_validation"])
        self.assertEqual(len(result["candidate_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
