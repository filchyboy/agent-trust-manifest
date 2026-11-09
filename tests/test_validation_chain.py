"""Offline consistency checks, not authentication or third-party validation."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/validation-chain"


class ValidationChainTests(unittest.TestCase):
    def setUp(self):
        self.raw = (EXAMPLE / "manifest.json").read_bytes()
        self.manifest = json.loads(self.raw)
        self.finding = (EXAMPLE / "assessor-finding.md").read_text()
        self.record = self.manifest["verification"]["verified_by"][0]

    def test_finding_names_exact_manifest_bytes(self):
        digest = re.search(r"SHA-256 \(exact fixture bytes\): `([a-f0-9]{64})`", self.finding)
        self.assertIsNotNone(digest)
        self.assertEqual(digest.group(1), hashlib.sha256(self.raw).hexdigest())

    def test_covered_claim_is_present_and_matches_illustration(self):
        self.assertEqual(self.record["covered_claims"],
                         ["interaction_profile.explicit_invocation_required"])
        claim = self.manifest
        for segment in self.record["covered_claims"][0].split("."):
            claim = claim[segment]
        self.assertIs(claim, True)
        self.assertIn("Assessed value: `true`", self.finding)

    def test_discovery_and_finding_refer_to_same_example(self):
        for value in [self.record["report_uri"], self.record["entity"],
                      self.manifest["manifest_version"], self.record["timestamp"]]:
            self.assertIn(value, self.finding)
        self.assertNotEqual(self.manifest["issuer"]["domain"], "assessor.example")

    def test_publisher_does_not_summarize_a_future_observation(self):
        observed = datetime.fromisoformat(self.record["timestamp"].replace("Z", "+00:00"))
        published = datetime.fromisoformat(self.manifest["published_at"].replace("Z", "+00:00"))
        self.assertLessEqual(observed, published)

    def test_fixture_does_not_claim_authentication_or_live_checks(self):
        self.assertIn("not an authenticated report", self.finding)
        self.assertIn("No controls were actually tested", self.finding)
        self.assertIn("**unverified**", self.finding)


if __name__ == "__main__":
    unittest.main()
