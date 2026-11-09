"""Exercise publisher-authentication outcomes through the consumer entry point."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.consumer import consume

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'examples/signing'
PUB = 'https://consumer-demo.example'
AT = '2026-10-06T18:00:00Z'


class AuthenticationPolicyTests(unittest.TestCase):
    def args(self, manifest=None, status=True, signed=True, finding=False):
        args = ['--manifest', str(manifest or FIX/'manifest.json'),
                '--expected-origin', PUB, '--at', AT]
        if status:
            args += ['--status-file', str(ROOT/'examples/consumer/operational-status.json')]
        if signed:
            args += ['--manifest-signature-file', str(FIX/'manifest.jws'),
                     '--manifest-keys-file', str(FIX/'publisher.jwks.json')]
        if finding:
            args += ['--finding-file', str(FIX/'finding.json'),
                     '--finding-signature-file', str(FIX/'finding.jws'),
                     '--assessor-keys-file', str(FIX/'assessor.jwks.json'),
                     '--assessor-origin', 'https://assessor.example',
                     '--trusted-assessor', 'https://assessor.example']
        return args

    def run_report(self, args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = consume.main(args)
        report = json.loads(output.getvalue())
        self.assertFalse(report['policy']['access_granted'])
        self.assertFalse(report['policy']['approval_granted'])
        return code, report

    def test_tampered_value_and_whitespace_hold_in_real_cli(self):
        original = (FIX/'manifest.json').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory)/'manifest.json'
            for data in (original.replace(b'"provenance_available": true',
                                          b'"provenance_available": false'), original+b' '):
                with self.subTest(tamper=data[-12:]):
                    manifest.write_bytes(data)
                    run = subprocess.run([sys.executable, str(ROOT/'tools/consumer/consume.py'),
                                          *self.args(manifest)], capture_output=True, text=True)
                    self.assertEqual(run.returncode, 1, run.stderr)
                    report = json.loads(run.stdout)
                    self.assertEqual(report['manifest_authentication'],
                                     {'state': 'invalid', 'reason': 'signature_mismatch'})
                    self.assertEqual(report['policy']['decision'], 'hold')
                    self.assertIn('manifest_signature_invalid:signature_mismatch', report['policy']['reasons'])
                    self.assertNotIn('issuer_authentication_unverified', report['policy']['reasons'])
                    self.assertFalse(report['policy']['access_granted'])
                    self.assertFalse(report['policy']['approval_granted'])

    def test_invalid_authentication_preserves_other_hold_reasons(self):
        with tempfile.TemporaryDirectory() as directory:
            signature = Path(directory)/'malformed.jws'
            signature.write_bytes(b'broken')
            args = self.args(status=False)
            args[args.index('--manifest-signature-file')+1] = str(signature)
            code, report = self.run_report(args)
        self.assertEqual(code, 1)
        self.assertEqual(report['policy']['decision'], 'hold')
        self.assertIn('status_file_not_supplied', report['policy']['reasons'])
        self.assertIn('manifest_signature_invalid:invalid_jws', report['policy']['reasons'])

    def test_accepted_assessor_finding_cannot_clear_invalid_publisher_hold(self):
        with tempfile.TemporaryDirectory() as directory:
            signature = Path(directory)/'bad.jws'
            signature.write_bytes(b'broken')
            args = self.args(finding=True)
            args[args.index('--manifest-signature-file')+1] = str(signature)
            code, report = self.run_report(args)
        self.assertEqual(code, 1)
        self.assertEqual(report['policy']['decision'], 'hold')
        self.assertEqual(report['assessor_finding']['acceptance'], 'accepted_for_claim')
        self.assertIn('manifest_signature_invalid:invalid_jws', report['policy']['reasons'])

    def test_valid_and_unrequested_authentication_preserve_triage(self):
        for signed, state in ((True, 'authenticated'), (False, 'unverified')):
            with self.subTest(signed=signed):
                code, report = self.run_report(self.args(signed=signed))
                self.assertEqual(code, 0)
                self.assertEqual(report['policy']['decision'], 'manual_review')
                self.assertEqual(report['manifest_authentication']['state'], state)
                self.assertIn('operational_status_revocation_not_checked', report['policy']['reasons'])
                self.assertFalse(report['status_evidence']['revocation_checked'])

    def test_missing_offline_file_is_unverified_not_unsigned_or_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.args()
            args[args.index('--manifest-signature-file')+1] = str(Path(directory)/'absent')
            code, report = self.run_report(args)
        self.assertEqual(code, 0)
        self.assertEqual(report['manifest_authentication'], {'state':'unverified', 'reason':'file_unavailable'})
        self.assertIn('issuer_authentication_unverified', report['policy']['reasons'])

    def test_network_absence_and_failures_remain_distinct_in_policy(self):
        manifest = (FIX/'manifest.json').read_bytes()
        now = consume.timestamp(AT)
        for error, state in [('signature_absent', 'unsigned'), ('fetch_timeout', 'unverified'),
                             ('network_failure', 'unverified'), ('http_failure', 'unverified')]:
            with self.subTest(error=error), patch.object(consume, 'fetch_manifest',
                    side_effect=[manifest, consume.ConsumerError(error)]) as fetch, \
                    patch.object(consume, 'datetime', wraps=consume.datetime) as clock:
                clock.now.return_value = now
                code, report = self.run_report(['--origin', PUB, '--authenticate-manifest',
                    '--status-file', str(ROOT/'examples/consumer/operational-status.json')])
                self.assertEqual(code, 0)
                self.assertEqual(report['policy']['decision'], 'manual_review')
                self.assertEqual(report['manifest_authentication'], {'state':state, 'reason':error})
                self.assertIn('issuer_authentication_unverified', report['policy']['reasons'])
                self.assertEqual([call.args for call in fetch.call_args_list], [(PUB,), (PUB, 'signature')])


if __name__ == '__main__':
    unittest.main()
