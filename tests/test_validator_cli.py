"""Regression tests for the optional CLI, not authentication or claim verification."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'tools/validator/validate.py'
SCHEMA = ROOT / 'schemas/agent-trust-manifest.schema.json'


class ValidatorCLI(unittest.TestCase):
    def run_cli(self, value, strict=False, schema=SCHEMA, raw=False):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text(value if raw else json.dumps(value))
            return subprocess.run([sys.executable, str(CLI), *(['--strict-formats'] if strict else []),
                                   str(path), str(schema)], capture_output=True, text=True)

    def manifest(self):
        return json.loads((ROOT / 'examples/basic-manifest.json').read_text())

    def test_valid_in_both_modes_without_deprecation(self):
        for strict in (False, True):
            result = self.run_cli(self.manifest(), strict)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('DeprecationWarning', result.stderr)

    def test_formats_are_explicit_and_all_errors_reported(self):
        value = self.manifest()
        value['issuer']['uri'] = 'not a uri'
        value['published_at'] = 'yesterday'
        self.assertEqual(self.run_cli(value).returncode, 0)
        result = self.run_cli(value, True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('/issuer/uri:', result.stderr)
        self.assertIn('/published_at:', result.stderr)
        self.assertLess(result.stderr.index('/issuer/uri:'), result.stderr.index('/published_at:'))

    def test_invalid_calendar_date(self):
        value = self.manifest(); value['published_at'] = '2026-02-30T12:00:00Z'
        self.assertEqual(self.run_cli(value, True).returncode, 1)

    def test_malformed_json_duplicate_keys_and_nonfinite(self):
        for raw in ('{', '{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            result = self.run_cli(raw, raw=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)

    def test_non_json_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bad.json'; path.write_bytes(b'\xff')
            result = subprocess.run([sys.executable, str(CLI), str(path), str(SCHEMA)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)

    def test_missing_file(self):
        result = subprocess.run([sys.executable, str(CLI), '/nonexistent/atm.json', str(SCHEMA)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)

    def test_wrong_type_and_missing_required(self):
        value = self.manifest(); value.pop('issuer'); value['interaction_profile']['explicit_invocation_required'] = 'yes'
        result = self.run_cli(value)
        self.assertEqual(result.returncode, 1)
        self.assertIn("'issuer' is a required property", result.stderr)
        self.assertIn('/interaction_profile/explicit_invocation_required:', result.stderr)

    def test_strict_formats_do_not_invent_crypto_or_version_rules(self):
        value = json.loads((ROOT / 'examples/signed-manifest.json').read_text())
        value['atm_version'] = 'banana'
        value['attestation']['alg'] = 'none'; value['attestation']['signature'] = ''
        value['verification'] = {'level': 'audit', 'verified_by': []}
        value['governance_artifacts'][0]['hash'] = ''
        self.assertEqual(self.run_cli(value, True).returncode, 0)

    def test_unresolved_reference_clean_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'test.schema.json'
            path.write_text(json.dumps({'$schema': 'https://json-schema.org/draft/2020-12/schema',
                                        '$ref': 'https://unreachable.invalid/never-fetch.json'}))
            result = self.run_cli({}, schema=path)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_invalid_schema_clean_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'test.schema.json'
            path.write_text('{"$schema":"https://json-schema.org/draft/2020-12/schema","type":42}')
            result = self.run_cli({}, schema=path)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)

    def test_unsupported_schema_shapes_and_dialects(self):
        for schema in (True, False, {'type': 'object'}, {'$schema': 'https://example.invalid/dialect'}):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'test.schema.json'; path.write_text(json.dumps(schema))
                result = self.run_cli({}, schema=path)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('Traceback', result.stderr)

    def test_invalid_neighbor_schema_clean_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'test.schema.json'
            root.write_text('{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object"}')
            (Path(directory)/'other.schema.json').write_text('{"type":"object"}')
            result = self.run_cli({}, schema=root)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
