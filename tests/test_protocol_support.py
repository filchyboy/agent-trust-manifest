"""Schema constraints and non-normative offline illustration; no protocol implementation."""
import contextlib
import copy
import io
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/consumer'))
import consume
import illustrate_protocol_support as demo

FIXTURES = ROOT / 'examples/consumer/protocol-support'
NOW = consume.timestamp('2026-10-06T18:00:00Z')
SCHEMA = 'protocol-support-draft-0.1.schema.json'


class ProtocolSupportTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((FIXTURES / 'declaration.json').read_text())
        self.context = (FIXTURES / 'expected-context.json').read_bytes()
        self.vocabulary = (FIXTURES / 'known-vocabulary.json').read_bytes()

    def illustrate(self, document=None, context=None, vocabulary=None):
        return demo.illustrate(json.dumps(self.doc if document is None else document).encode(),
                               self.context if context is None else context,
                               self.vocabulary if vocabulary is None else vocabulary, NOW)

    def assert_no_authority(self, report):
        for field in ['access_granted', 'approval_granted', 'interoperability_verified',
                      'runtime_enforcement_performed', 'requirements_satisfied']:
            self.assertFalse(report[field], field)
        self.assertEqual(report['caller_eligibility'], 'unresolved')

    def test_schema_and_illustration_cases_are_separate(self):
        cases = json.loads((FIXTURES / 'cases.json').read_text())
        for case in cases:
            document = copy.deepcopy(self.doc)
            for path,value in case['changes'].items():
                keys=path.split('.')
                target=document
                for key in keys[:-1]:
                    target=target[int(key)] if isinstance(target,list) else target[key]
                target[int(keys[-1]) if isinstance(target,list) else keys[-1]]=value
            for path in case['remove']:
                keys=path.split('.')
                target=document
                for key in keys[:-1]:
                    target=target[int(key)] if isinstance(target,list) else target[key]
                del target[int(keys[-1]) if isinstance(target,list) else keys[-1]]
            with self.subTest(case=case['name']), patch.object(
                    consume.subprocess,'run',side_effect=AssertionError('Offline only')):
                self.assertEqual(consume.validate(document,SCHEMA),case['schema_valid'])
                report=self.illustrate(document)
                self.assertEqual(report['state'],case['illustration_state'])
                self.assertEqual(report['reason'],case['reason'])
                self.assert_no_authority(report)

    def test_discovery_fixture_pins_declaration_without_asserting_trust(self):
        manifest=json.loads((FIXTURES/'manifest.json').read_text())
        self.assertTrue(consume.validate(manifest,'agent-trust-manifest.schema.json'))
        ref=manifest['governance_artifacts'][1]
        self.assertEqual(ref['type'],'platform_policy')
        self.assertEqual(ref['version'],self.doc['profile_version'])
        self.assertEqual(ref['schema_uri'],
                         'https://agenttrustmanifest.org/schemas/'+SCHEMA)
        self.assertEqual(ref['hash'],'sha256:'+hashlib.sha256(
            (FIXTURES/'declaration.json').read_bytes()).hexdigest())
        self.assertEqual(ref['subject'],self.doc['applies_to']['subject'])
        self.assertEqual(ref['scope'],{'level':'capability',
                                     'identifier':self.doc['applies_to']['capability_id']})
        self.assertEqual(manifest['manifest_version'],self.doc['manifest_version'])
        self.assertEqual(ref['assurance_level'],'declaration')
        self.assertEqual(ref['revocation_status'],'unknown')

    def test_multiple_mechanisms_versions_profiles_and_distinct_links(self):
        report=self.illustrate()
        self.assertEqual(len(report['mechanisms']),3)
        for key,value in self.doc['mechanisms'].items():
            self.assertEqual(report['mechanisms'][key]['version'],value['version'])
            self.assertEqual(report['mechanisms'][key]['profile'],value['profile'])
            self.assertNotIn(value['specification_uri'],value['endpoint_uris'])
            self.assertNotIn(value['specification_uri'],value['documentation_uris'])
        self.assert_no_authority(report)

    def test_scope_is_single_exact_binding_not_inherited(self):
        for key in ['tenant','surface','deployment','policy_version']:
            with self.subTest(key=key):
                context=json.loads(self.context)
                context['scope'][key]='another-context'
                self.assertEqual(self.illustrate(context=json.dumps(context).encode())['reason'],
                                 'applicability_mismatch')
        self.doc['mechanisms']['recognition_a']['applies_to']=copy.deepcopy(self.doc['applies_to'])
        self.assertFalse(consume.validate(self.doc,SCHEMA))

    def test_no_vocabulary_does_not_mean_adapter_support(self):
        report=self.illustrate(vocabulary=b'{"recognized_tuples":[]}')
        self.assertEqual(report['reason'],'required_mechanism_unresolved')
        self.assert_no_authority(report)
        self.doc['requirements']=[]
        report=self.illustrate(vocabulary=b'{"recognized_tuples":[]}')
        self.assertEqual(report['state'],'declarations_read')
        self.assertFalse(any(x['vocabulary_match'] for x in report['mechanisms'].values()))
        self.assert_no_authority(report)

    def test_same_protocol_different_explicit_versions_are_distinct(self):
        item=copy.deepcopy(self.doc['mechanisms']['payment_a'])
        item['version']='2.0'
        self.doc['mechanisms']['payment_v2']=item
        self.assertTrue(consume.validate(self.doc,SCHEMA))
        report=self.illustrate()
        self.assertFalse(report['mechanisms']['payment_v2']['vocabulary_match'])
        self.assertTrue(report['mechanisms']['payment_a']['vocabulary_match'])

    def test_duplicate_tuple_is_ambiguous_even_with_different_keys(self):
        self.doc['mechanisms']['payment_copy']=copy.deepcopy(self.doc['mechanisms']['payment_a'])
        self.doc['mechanisms']['payment_copy']['support']='unsupported'
        # JSON Schema checks shape; cross-entry identity uniqueness is a separate semantic rule.
        self.assertTrue(consume.validate(self.doc,SCHEMA))
        self.assertEqual(self.illustrate()['reason'],'ambiguous_mechanism_identity')

    def test_test_reference_is_not_independently_verified_support(self):
        self.doc['mechanisms']['payment_a']['test_report']={
            'uri':'https://assessments.example/report-1',
            'assessor_id':'urn:example:assessor','relationship':'independent'}
        report=self.illustrate()
        self.assertEqual(report['mechanisms']['payment_a']['independent_testing'],'unverified')
        self.assertEqual(report['authentication'],'unverified')
        self.assert_no_authority(report)

    def test_existing_platform_refusal_is_never_overridden(self):
        manifest=json.loads((ROOT/'examples/consumer/platform-controls/manifest.json').read_text())
        controls=json.loads((ROOT/'examples/consumer/platform-controls/profile.json').read_text())
        controls['capabilities'][0]['platform_permission']='refused'
        raw=json.dumps(controls).encode()
        manifest['governance_artifacts'][1]['hash']='sha256:'+hashlib.sha256(raw).hexdigest()
        previous=consume.inspect(json.dumps(manifest).encode(),
                                 (ROOT/'examples/consumer/operational-status.json').read_bytes(),
                                 'https://consumer-demo.example',NOW,raw,json.loads(self.context))
        self.assertEqual(previous['platform_controls']['reason'],'platform_refusal_declared')
        before=copy.deepcopy(previous)
        report=self.illustrate()
        self.assertEqual(previous,before)
        self.assertEqual(previous['policy']['decision'],'hold')
        self.assertFalse(previous['policy']['access_granted'])
        self.assert_no_authority(report)

    def test_old_profile_cannot_silently_accept_typed_protocol_fields(self):
        old=json.loads((ROOT/'examples/consumer/platform-controls/profile.json').read_text())
        self.assertTrue(consume.validate(old,'platform-controls-draft-0.1.schema.json'))
        old['capabilities'][0]['protocol_support']=self.doc['mechanisms']
        self.assertFalse(consume.validate(old,'platform-controls-draft-0.1.schema.json'))
        self.assertFalse(consume.validate(self.doc,'agent-trust-manifest.schema.json'))

    def test_cli_illustration_and_malformed_input(self):
        args=['--declaration-file',str(FIXTURES/'declaration.json'),
              '--expected-context-file',str(FIXTURES/'expected-context.json'),
              '--known-vocabulary-file',str(FIXTURES/'known-vocabulary.json'),
              '--at','2026-10-06T18:00:00Z']
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code=demo.main(args)
        self.assertEqual(code,0)
        self.assert_no_authority(json.loads(output.getvalue()))
        self.assertEqual(demo.illustrate(b'{',self.context,self.vocabulary,NOW)['state'],'unresolved')
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code=demo.main(args+['--declaration-file',str(FIXTURES/'not-present.json')])
        self.assertEqual(code,1)
        self.assert_no_authority(json.loads(output.getvalue()))


if __name__=='__main__':
    unittest.main()
