"""Consistency of illustrative mapping data, not a production mapping implementation."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/rating-normalization"


class RatingNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.source_bytes = (FIXTURE / "provider-native.json").read_bytes()
        self.source = json.loads(self.source_bytes)
        self.mapping = json.loads((FIXTURE / "mapping.json").read_text())
        self.feed = json.loads((FIXTURE / "normalized-feed.json").read_text())
        self.schema = json.loads((ROOT / "schemas/reputation-feed.schema.json").read_text())

    def test_native_grade_maps_to_existing_enum(self):
        allowed = self.schema["properties"]["overall"]["properties"]["rating"]["enum"]
        native = self.source["grade"]["label"]
        self.assertNotIn(native, allowed)
        self.assertEqual(self.mapping["map"][native], self.feed["overall"]["rating"])
        for rating in list(self.mapping["map"].values()) + [self.mapping["unmapped"]]:
            self.assertIn(rating, allowed)
        self.assertEqual(self.mapping["unmapped"], "unknown")

    def test_source_provenance_is_preserved(self):
        ref = self.feed["evidence_refs"][0]
        self.assertEqual(ref["uri"], self.mapping["source_uri"])
        self.assertEqual(ref["hash"], "sha256:" + hashlib.sha256(self.source_bytes).hexdigest())
        self.assertEqual(self.feed["methodology"]["id"], self.mapping["mapping_id"])
        self.assertEqual(self.feed["methodology"]["version"], self.mapping["mapping_version"])
        self.assertEqual(self.source["grade"]["scale"], self.mapping["source_scale"])

    def test_example_does_not_convert_business_grade_into_control_assessment(self):
        self.assertEqual(self.feed["dimensions"], [])
        self.assertNotIn("result", self.feed["overall"])
        self.assertEqual(self.feed["subject"]["id"], self.source["business_reference"])
        self.assertEqual(self.feed["scope"], {"level": "tenant", "identifier": self.source["business_reference"]})

    def test_example_does_not_claim_real_authentication(self):
        self.assertEqual(self.feed["issuer"]["id"], self.mapping["normalizer"])
        self.assertEqual(self.feed["assurance_level"], "declaration")
        self.assertEqual(self.feed["revocation_status"], "unknown")
        self.assertEqual(self.feed["signature"]["value"], "NOT-A-REAL-SIGNATURE")
        self.assertTrue(self.mapping["fixture_only"])


if __name__ == "__main__":
    unittest.main()
