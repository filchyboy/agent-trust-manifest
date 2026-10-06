"""Regression checks for implementation-defined artifact responsibility labels."""
import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]


class ArtifactOwnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schemas = [json.loads(p.read_text()) for p in (ROOT / "schemas").glob("*.schema.json")]
        registry = Registry().with_resources(
            (schema["$id"], Resource.from_contents(schema)) for schema in schemas
        )
        core = json.loads((ROOT / "schemas/agent-trust-manifest.schema.json").read_text())
        cls.validator = Draft202012Validator(core, registry=registry)
        cls.fixture = json.loads((ROOT / "examples/signed-manifest.json").read_text())

    def with_owner(self, value):
        document = copy.deepcopy(self.fixture)
        document["governance_artifacts"][0]["owner"] = value
        return document

    def test_custom_neutral_labels(self):
        for label in ["example_catalog_team", "example_ratings_team", "fictional_component_42"]:
            with self.subTest(label=label):
                self.assertTrue(self.validator.is_valid(self.with_owner(label)))

    def test_empty_and_whitespace_only_rejected(self):
        for label in ["", " ", "\t", "\n", " \t\r\n", "\u00a0"]:
            with self.subTest(label=repr(label)):
                self.assertFalse(self.validator.is_valid(self.with_owner(label)))

    def test_nonstring_rejected(self):
        for value in [None, 42, True, [], {}, 1.5]:
            with self.subTest(value=value):
                self.assertFalse(self.validator.is_valid(self.with_owner(value)))

    def test_missing_owner_rejected(self):
        document = copy.deepcopy(self.fixture)
        del document["governance_artifacts"][0]["owner"]
        self.assertFalse(self.validator.is_valid(document))

    def test_existing_artifact_shape_preserved(self):
        # Fictional historical-style fixture keeps the same owner field and metadata shape.
        document = self.with_owner("example_legacy_component")
        self.assertTrue(self.validator.is_valid(document))
        self.assertEqual(
            set(document["governance_artifacts"][0]),
            set(self.fixture["governance_artifacts"][0]),
        )

    def test_nonblank_whitespace_surrounding_label_is_valid(self):
        self.assertTrue(self.validator.is_valid(self.with_owner("  example_component\t")))

    def test_basic_manifest_without_artifacts_remains_valid(self):
        document = json.loads((ROOT / "examples/basic-manifest.json").read_text())
        self.assertTrue(self.validator.is_valid(document))


if __name__ == "__main__":
    unittest.main()
