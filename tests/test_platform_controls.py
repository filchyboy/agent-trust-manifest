"""Offline issue #1 acceptance fixtures; no action or approval implementation."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/consumer'))
import consume

FIXTURES = ROOT / 'examples/consumer'
PLATFORM = FIXTURES / 'platform-controls'
ORIGIN = 'https://consumer-demo.example'
NOW = consume.timestamp('2026-10-06T18:00:00Z')


class PlatformControlTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((PLATFORM / 'manifest.json').read_text())
        self.status = (FIXTURES / 'operational-status.json').read_bytes()
        self.profile = json.loads((PLATFORM / 'profile.json').read_text())
        self.expected = json.loads((PLATFORM / 'expected-context.json').read_text())

    def inspect(self, profile=None, expected=None):
        raw = json.dumps(profile if profile is not None else self.profile).encode()
        self.manifest['governance_artifacts'][1]['hash'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
        return consume.inspect(json.dumps(self.manifest).encode(), self.status, ORIGIN, NOW,
                               raw,
                               expected if expected is not None else self.expected)

    def assert_no_authority(self, report):
        self.assertFalse(report['policy']['access_granted'])
        self.assertFalse(report['policy']['approval_granted'])
        self.assertFalse(report['policy']['runtime_enforcement_performed'])
        self.assertEqual(report['policy']['caller_eligibility'], 'unresolved')
        self.assertEqual(report['platform_controls']['authentication'], 'unverified')

    def test_acceptance_fixture_matrix(self):
        cases = json.loads((PLATFORM / 'cases.json').read_text())
        for case in cases:
            with self.subTest(case=case['name']), patch.object(
                    consume.subprocess, 'run', side_effect=AssertionError('No network or action allowed')):
                profile = copy.deepcopy(self.profile)
                for path, value in case['changes'].items():
                    parts = path.split('.')
                    target = profile
                    for key in parts[:-1]:
                        target = target[int(key)] if isinstance(target, list) else target[key]
                    target[parts[-1]] = value
                report = self.inspect(profile)
                self.assertEqual(report['policy']['decision'], case['decision'])
                self.assertEqual(report['platform_controls']['reason'], case['reason'])
                self.assert_no_authority(report)

    def test_capability_discovery_exposes_prerequisites_without_fulfilling_them(self):
        report = self.inspect()
        cap = report['platform_controls']['capability']
        self.assertTrue(cap['approval_required'])
        self.assertEqual(cap['access_conditions'], self.profile['capabilities'][0]['access_conditions'])
        self.assertEqual(report['platform_controls']['capability_existence'], 'declared')
        self.assertFalse(report['platform_controls']['approval_granted'])
        self.assert_no_authority(report)

    def test_operator_consent_and_ability_cannot_override_platform_refusal_or_approval(self):
        # Operator consent/agent ability are external facts, never ATM mandate fields.
        for permission in ['allowed', 'refused']:
            with self.subTest(permission=permission):
                self.profile['capabilities'][0]['platform_permission'] = permission
                report = self.inspect()
                self.assertTrue(report['platform_controls']['capability']['approval_required'])
                self.assert_no_authority(report)
                self.assertEqual(report['policy']['decision'],
                                 'hold' if permission == 'refused' else 'manual_review')

    def test_profile_and_evidence_must_each_match_independent_expectation(self):
        for field in ['deployment', 'tenant', 'surface', 'policy_version']:
            with self.subTest(field=field):
                profile = copy.deepcopy(self.profile)
                profile['scope'][field] = 'different'
                profile['evidence'][0]['applies_to']['scope'][field] = 'different'
                report = self.inspect(profile)
                self.assertEqual(report['platform_controls']['reason'], 'profile_' + field + '_mismatch')
                self.assertEqual(report['policy']['decision'], 'hold')
        expected = copy.deepcopy(self.expected)
        expected['subject']['type'] = 'agent'
        self.assertEqual(self.inspect(expected=expected)['platform_controls']['reason'],
                         'expected_context_missing_or_invalid')

    def test_publisher_and_subject_need_not_be_same_identity(self):
        self.assertNotEqual(self.profile['publisher'], self.profile['subject'])
        report = self.inspect()
        self.assertTrue(report['platform_controls']['declaration_checks_passed'])
        self.assert_no_authority(report)

    def test_all_roles_and_applicability_fields_required(self):
        for field in ['publisher', 'subject', 'scope', 'control_authority', 'enforcement_point']:
            with self.subTest(field=field):
                profile = copy.deepcopy(self.profile)
                del profile[field]
                self.assertFalse(consume.validate(profile, 'platform-controls-draft-0.1.schema.json'))
        del self.profile['evidence'][0]['assessor']
        self.assertFalse(consume.validate(self.profile, 'platform-controls-draft-0.1.schema.json'))

    def test_matching_agent_identifier_never_satisfies_legacy_platform_status(self):
        for where in ['reference', 'status']:
            with self.subTest(where=where):
                manifest = copy.deepcopy(self.manifest)
                status = json.loads(self.status)
                if where == 'reference':
                    manifest['governance_artifacts'][0]['subject']['type'] = 'agent'
                else:
                    status['subject']['type'] = 'agent'
                raw = json.dumps(status).encode()
                manifest['governance_artifacts'][0]['hash'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
                report = consume.inspect(json.dumps(manifest).encode(), raw, ORIGIN, NOW)
                self.assertEqual(report['policy']['decision'], 'hold')
                self.assertFalse(report['status_evidence']['prerequisites_met'])

    def test_legacy_status_does_not_ignore_unsupported_subject_qualifiers(self):
        for qualifier in ['deployment', 'tenant', 'surface', 'capability_id']:
            for where in ['reference', 'status']:
                with self.subTest(qualifier=qualifier, where=where):
                    manifest = copy.deepcopy(self.manifest)
                    status = json.loads(self.status)
                    subject = (manifest['governance_artifacts'][0]['subject']
                               if where == 'reference' else status['subject'])
                    subject[qualifier] = 'other-scope'
                    raw = json.dumps(status).encode()
                    manifest['governance_artifacts'][0]['hash'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
                    report = consume.inspect(json.dumps(manifest).encode(), raw, ORIGIN, NOW)
                    self.assertEqual(report['policy']['decision'], 'hold')

    def test_missing_and_stale_are_unresolved_not_absent_capability(self):
        for raw in [None, b'{}']:
            result = consume.inspect_platform_controls(raw, self.expected, self.manifest, ORIGIN, NOW)
            self.assertEqual(result['state'], 'unresolved')
            self.assertEqual(result['capability_existence'], 'unresolved')
        self.profile['expires_at'] = '2026-10-06T18:00:00Z'
        self.assertEqual(self.inspect()['platform_controls']['capability_existence'], 'unresolved')

    def test_ambiguous_capabilities_and_assessments_are_held(self):
        for key in ['capabilities', 'evidence']:
            with self.subTest(key=key):
                profile = copy.deepcopy(self.profile)
                profile[key].append(copy.deepcopy(profile[key][0]))
                self.assertEqual(self.inspect(profile)['policy']['decision'], 'hold')

    def test_legacy_core_stays_valid_and_draft_is_not_silently_a_core_field(self):
        self.assertTrue(consume.validate(self.manifest, 'agent-trust-manifest.schema.json'))
        self.manifest['platform_controls'] = self.profile
        self.assertFalse(consume.validate(self.manifest, 'agent-trust-manifest.schema.json'))

    def test_cli_profile_and_separate_expectation_are_paired(self):
        args = ['--manifest', str(PLATFORM / 'manifest.json'), '--expected-origin', ORIGIN,
                '--status-file', str(FIXTURES / 'operational-status.json'),
                '--at', '2026-10-06T18:00:00Z', '--platform-profile-file', str(PLATFORM / 'profile.json')]
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = consume.main(args)
        self.assertEqual(code, 1)
        self.assertIn('profile_and_expected_context_required', output.getvalue())
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = consume.main(args + ['--expected-context-file', str(PLATFORM / 'expected-context.json')])
        self.assertEqual(code, 0)
        self.assert_no_authority(json.loads(output.getvalue()))

    def test_cli_sidecar_and_context_errors_preserve_manifest_and_status(self):
        args = ['--manifest', str(PLATFORM / 'manifest.json'), '--expected-origin', ORIGIN,
                '--status-file', str(FIXTURES / 'operational-status.json'),
                '--at', '2026-10-06T18:00:00Z']
        with tempfile.TemporaryDirectory() as directory:
            bad_context = Path(directory) / 'malformed.json'
            bad_context.write_text('{')
            missing = str(Path(directory) / 'missing.json')
            for profile, context, reason in [
                (missing, str(PLATFORM / 'expected-context.json'), 'platform_profile_file_unavailable'),
                (str(PLATFORM / 'profile.json'), missing, 'expected_context_file_unavailable'),
                (str(PLATFORM / 'profile.json'), str(bad_context),
                 'expected_context_invalid_or_overcomplex_json'),
            ]:
                with self.subTest(reason=reason), contextlib.redirect_stdout(io.StringIO()) as output:
                    code = consume.main(args + ['--platform-profile-file', profile,
                                                '--expected-context-file', context])
                report = json.loads(output.getvalue())
                self.assertEqual(code, 1)
                self.assertEqual(report['manifest']['state'], 'fresh')
                self.assertEqual(report['status_evidence']['digest'], 'matched')
                self.assertEqual(report['platform_controls']['state'], 'unresolved')
                self.assertEqual(report['platform_controls']['reason'], reason)
                self.assertIn(reason, report['policy']['reasons'])
                self.assert_no_authority(report)

    def test_profile_digest_mismatch_and_missing_reference_hold(self):
        raw = (PLATFORM / 'profile.json').read_bytes() + b' '
        result = consume.inspect_platform_controls(raw, self.expected, self.manifest, ORIGIN, NOW)
        self.assertEqual(result['reason'], 'profile_digest_mismatch')
        self.manifest['governance_artifacts'].pop()
        result = consume.inspect_platform_controls(raw, self.expected, self.manifest, ORIGIN, NOW)
        self.assertEqual(result['reason'], 'platform_profile_reference_missing_or_ambiguous')

    def test_bad_status_cannot_be_rescued_by_positive_profile(self):
        self.status = (FIXTURES / 'tampered-status.json').read_bytes()
        report = self.inspect()
        self.assertEqual(report['policy']['decision'], 'hold')
        self.assert_no_authority(report)


if __name__ == '__main__':
    unittest.main()
