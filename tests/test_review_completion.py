"""Remaining-review coverage: portable offline consumption, visitor policy and validation modes."""
import contextlib
import io
import ipaddress
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tools.signing.check_consumer_vectors import check
from tools.consumer import consume
from tools.validator import check_examples

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'examples/signing'


class ReviewCompletion(unittest.TestCase):
    def test_shared_consumer_and_origin_contract(self):
        result=check(FIX)
        self.assertTrue(result['passed'],result['failures'])
        self.assertEqual((result['consumer_cases'],result['origin_cases']),(56,159))

    def test_explicit_structural_mode_preserves_default_and_modes_are_exclusive(self):
        import tempfile
        value=json.loads((FIX/'manifest.json').read_bytes());value['issuer']['uri']='not a URI'
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'manifest.json';path.write_text(json.dumps(value))
            args=[sys.executable,str(ROOT/'tools/validator/validate.py')]
            rest=[str(path),str(ROOT/'schemas/agent-trust-manifest.schema.json')]
            self.assertEqual(subprocess.run([*args,*rest],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run([*args,'--structural-only',*rest],capture_output=True).returncode,0)
            self.assertEqual(subprocess.run([*args,'--strict-formats',*rest],capture_output=True).returncode,1)
            self.assertEqual(subprocess.run([*args,'--strict-formats','--structural-only',*rest],capture_output=True).returncode,2)

    def test_all_distinct_authoring_examples_pass_explicit_strict_mode(self):
        catalog=json.loads((ROOT/'tools/validator/example-cases.json').read_bytes())['cases']
        self.assertEqual(len(catalog),25)
        self.assertEqual(len({(c['document'],c['schema']) for c in catalog}),25)
        output=io.StringIO()
        with contextlib.redirect_stdout(output): code=check_examples.main(['--strict-formats'])
        self.assertEqual(code,0,output.getvalue())
        self.assertEqual(json.loads(output.getvalue().splitlines()[-1])['mode'],'strict-formats')

    def test_visitor_age_limit_does_not_change_signature_authentication_or_grant_access(self):
        args=['--manifest',str(FIX/'manifest.json'),'--expected-origin','https://consumer-demo.example',
              '--at','2026-10-06T18:00:00Z','--status-file',str(ROOT/'examples/consumer/operational-status.json'),
              '--manifest-signature-file',str(FIX/'manifest.jws'),'--manifest-keys-file',str(FIX/'publisher.jwks.json'),
              '--finding-file',str(FIX/'finding.json'),'--finding-signature-file',str(FIX/'finding.jws'),
              '--assessor-keys-file',str(FIX/'assessor.jwks.json'),'--assessor-origin','https://assessor.example',
              '--trusted-assessor','https://assessor.example','--max-finding-age-seconds','299']
        output=io.StringIO()
        with contextlib.redirect_stdout(output): consume.main(args)
        report=json.loads(output.getvalue())
        finding=report['assessor_finding']
        self.assertEqual(finding['authentication']['state'],'authenticated')
        self.assertEqual(finding['applicability'],'matched')
        self.assertEqual(finding['reason'],'finding_observation_too_old')
        self.assertEqual(finding['acceptance'],'unresolved')
        self.assertFalse(report['policy']['access_granted'])
        self.assertNotIn('accepted_for_claim',report['policy']['claim_acceptance'].values())

    def test_age_option_without_finding_is_an_explicit_unresolved_input(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            consume.main(['--manifest',str(FIX/'manifest.json'),'--expected-origin','https://consumer-demo.example',
                          '--at','2026-10-06T18:00:00Z','--max-finding-age-seconds','10'])
        report=json.loads(output.getvalue())
        self.assertEqual(report['assessor_finding']['reason'],'finding_inputs_required')
        self.assertFalse(report['policy']['access_granted'])

    def test_public_address_snapshot_matches_the_selected_python_runtime_tables(self):
        policy=json.loads((ROOT/'tools/independent-verifier/ip-policy-v1.json').read_bytes())
        for family,constants in [('ipv4',ipaddress._IPv4Constants),('ipv6',ipaddress._IPv6Constants)]:
            self.assertEqual(set(policy[family]['private']),{str(n) for n in constants._private_networks})
            self.assertEqual(set(policy[family]['private_exceptions']),{str(n) for n in constants._private_networks_exceptions})
            if family=='ipv4':
                expected={str(n) for n in [constants._public_network,constants._reserved_network,
                    constants._multicast_network,constants._loopback_network,constants._linklocal_network]}
            else:
                expected={str(n) for n in constants._reserved_networks}|{'::ffff:0:0/96','2002::/16','2001::/32',
                    str(constants._multicast_network),str(constants._linklocal_network),'::/128','::1/128'}
            self.assertEqual(set(policy[family]['always_reject']),expected)


if __name__=='__main__': unittest.main()
