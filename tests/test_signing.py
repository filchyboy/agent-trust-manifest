"""Profile attack cases, explicit trust boundaries, CLI, and independent shared vectors."""
import copy
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
from tools.signing import atm_signing as p
from tools.consumer import consume
from tools.consumer import fetch_manifest as net

FIX = ROOT / "examples/signing"
NOW = 1791309600
PUB = "https://consumer-demo.example"
ASS = "https://assessor.example"


def raw(value):
    return json.dumps(value, separators=(",", ":")).encode()


class SigningTests(unittest.TestCase):
    def setUp(self):
        self.manifest = (FIX / "manifest.json").read_bytes()
        self.sig = (FIX / "manifest.jws").read_bytes()
        self.keys = (FIX / "publisher.jwks.json").read_bytes()
        self.finding = (FIX / "finding.json").read_bytes()
        self.fsig = (FIX / "finding.jws").read_bytes()
        self.fkeys = (FIX / "assessor.jwks.json").read_bytes()

    def verify(self, payload=None, sig=None, keys=None, issuer=PUB, kind=p.MANIFEST, now=NOW):
        return p.verify(self.manifest if payload is None else payload, self.sig if sig is None else sig,
                        self.keys if keys is None else keys, issuer, kind, now)

    def altered_header(self, field, value):
        protected, _, signature = self.sig.split(b".")
        h = p.document(p.unb64(protected.decode()))
        h[field] = value
        return p.b64(raw(h)).encode() + b".." + signature

    def finding_result(self, value=None, sig=None, keys=None, manifest=None, issuer=ASS, trusted=None):
        payload = self.finding if value is None else raw(value)
        if value is not None and sig is None:
            sig = p.sign(payload, bytes(range(32, 64)), ASS, p.FINDING, 'fictional-1',
                         1791309300, 1791313200)
        return p.inspect_finding(payload, self.fsig if sig is None else sig,
            self.fkeys if keys is None else keys, self.manifest if manifest is None else manifest,
            PUB, issuer, [ASS] if trusted is None else trusted, NOW)

    def test_shared_vectors_and_independent_node_reverse_signatures(self):
        run = subprocess.run(['node', str(ROOT / 'tools/signing/interop.mjs'), str(FIX)],
                             capture_output=True, check=True, text=True)
        output = json.loads(run.stdout)
        vectors = json.loads((FIX / 'vectors.json').read_text())['vectors']
        self.assertEqual(len(output), 2)
        checked = {c['id'] for result in output for c in result['negative_vectors'] if c['rejected']}
        expected = {c['id'] for c in json.loads((FIX / 'vectors.json').read_text())['negative_vectors']
                    if c['independent_crypto']}
        self.assertEqual(checked, expected)
        self.assertEqual(len(checked), 4)
        for v, other in zip(vectors, output):
            self.assertTrue(other['verified'] and other['tamper_rejected'])
            p.verify((FIX / v['payload']).read_bytes(), other['node_jws'].encode(),
                     (FIX / v['jwks']).read_bytes(), v['origin'], v['type'], v['now'])

    def test_tampered_manifest_bytes(self):
        with self.assertRaisesRegex(p.VerificationError, 'signature_mismatch'):
            self.verify(payload=self.manifest + b' ')

    def test_wrong_origin_type_key_and_algorithm(self):
        for kwargs in ({'issuer':ASS}, {'kind':p.FINDING}, {'keys':self.fkeys}):
            with self.subTest(kwargs=kwargs), self.assertRaises(p.VerificationError):
                self.verify(**kwargs)
        for alg in ('none', 'EdDSA', 'RS256', 'Ed448'):
            with self.subTest(alg=alg), self.assertRaisesRegex(p.VerificationError, 'unsupported_profile'):
                self.verify(sig=self.altered_header('alg',alg))
        with self.assertRaisesRegex(p.VerificationError, 'unknown_key'):
            self.verify(sig=self.altered_header('kid','unknown'))

    def test_forbidden_headers_and_critical_parameters(self):
        for field, value in [('b64',True),('crit',['b64']),('crit',['b64','unknown']),
                             ('jku','https://evil.example/key'),('jwk',{}),('x5u','https://evil.example')]:
            with self.subTest(field=field), self.assertRaises(p.VerificationError):
                self.verify(sig=self.altered_header(field,value))

    def test_expired_future_and_typed_times(self):
        for field, value in [('exp',NOW),('iat',NOW+1),('exp',True),('iat',1791306000.0),
                             ('exp','1791313200'),('iat',-1),('exp',253402300800)]:
            with self.subTest(field=field,value=value), self.assertRaisesRegex(p.VerificationError,'invalid_signature_time'):
                self.verify(sig=self.altered_header(field,value))
        with self.assertRaises(p.VerificationError):
            self.verify(now=1791313200)

    def test_revoked_compromised_key_cannot_backdate(self):
        for status in ('revoked','compromised'):
            keys = p.document(self.keys)
            keys['keys'][0]['status'] = status
            with self.subTest(status=status), self.assertRaisesRegex(p.VerificationError,'revoked_key'):
                self.verify(keys=raw(keys))  # Signature iat predates key snapshot and NOW.

    def test_rotation_retirement_distinct_from_compromise(self):
        keys=p.document(self.keys)
        keys['keys'][0].update(status='retired',retired_at=NOW-1)
        self.verify(keys=raw(keys))
        sig=p.sign(self.manifest, bytes(range(32)),PUB,p.MANIFEST,'fictional-1',NOW, NOW+100)
        with self.assertRaisesRegex(p.VerificationError,'retired_key'):
            self.verify(sig=sig,keys=raw(keys))

    def test_jwks_expired_future_window_key_time(self):
        for field,value in [('expires_at',NOW),('issued_at',NOW+1),('issued_at',True),('expires_at',NOW+86401)]:
            k=p.document(self.keys); k[field]=value
            with self.subTest(field=field), self.assertRaises(p.VerificationError):
                self.verify(keys=raw(k))
        for field,value in [('nbf',NOW),('exp',NOW),('exp',False)]:
            k=p.document(self.keys); k['keys'][0][field]=value
            with self.subTest(field=field), self.assertRaises(p.VerificationError):
                self.verify(keys=raw(k))

    def test_wrong_public_key_under_same_origin_and_kid(self):
        k=p.document(self.keys)
        k['keys'][0]['x']=p.document(self.fkeys)['keys'][0]['x']
        with self.assertRaisesRegex(p.VerificationError,'signature_mismatch'):
            self.verify(keys=raw(k))

    def test_revoked_assessor_key_never_accepts_finding(self):
        k=p.document(self.fkeys);k['keys'][0]['status']='compromised'
        result=self.finding_result(keys=raw(k))
        self.assertEqual(result['authentication']['reason'],'revoked_key')
        self.assertEqual(result['acceptance'],'unresolved')

    def test_correctly_signed_unusual_field_types_fail_cleanly(self):
        values=[None,True,0,1.5,[],{},'']
        for field in p.document(self.finding):
            for value in values:
                f=p.document(self.finding);f[field]=value
                with self.subTest(field=field,value=value):
                    self.assertEqual(self.finding_result(f)['acceptance'],'unresolved')
        for field in p.document(self.keys)['keys'][0]:
            for value in values:
                if field == 'nbf' and type(value) is int and value == 0:
                    continue  # Epoch is a valid not-before time.
                k=p.document(self.keys);k['keys'][0][field]=value
                with self.subTest(keyfield=field,value=value), self.assertRaises(p.VerificationError):
                    self.verify(keys=raw(k))

    def test_signature_and_keyset_size_limits(self):
        with self.assertRaisesRegex(p.VerificationError,'invalid_jws'):
            self.verify(sig=b'x'*4097)
        with self.assertRaisesRegex(p.VerificationError,'document_too_large'):
            self.verify(keys=b'x'*16385)

    def test_malformed_public_keyset(self):
        for field,value in [('x',p.b64(b'X'*31)),('x','a='),('d','private'),('status','unknown'),
                             ('kid',[]),('kty','RSA'),('alg','EdDSA'),('retired_at',NOW)]:
            k=p.document(self.keys); k['keys'][0][field]=value
            with self.subTest(field=field), self.assertRaises(p.VerificationError):
                self.verify(keys=raw(k))
        for count in (0,2,17):
            k=p.document(self.keys); k['keys']=k['keys']*count
            with self.subTest(count=count), self.assertRaises(p.VerificationError):
                self.verify(keys=raw(k))

    def test_duplicate_json_and_overcomplex_or_nonfinite_payload(self):
        for value in [b'{"a":1,"a":2}',b'{"x":NaN}',b'{"x":1e999}',b'{"x":"\\ud800"}',
                      b'\xef\xbb\xbf{}', b'[]',b'{"a":'+b'['*18+b'0'+b']'*18+b'}',
                      raw({'x':'a'*2049}),raw({'x':[0]*129}),b' '*65537]:
            with self.subTest(value=value[:30]), self.assertRaises(p.VerificationError):
                self.verify(payload=value)
        protected,_,sig=self.sig.split(b'.')
        h=p.unb64(protected.decode())[:-1]+b',"alg":"Ed25519"}'
        with self.assertRaisesRegex(p.VerificationError,'duplicate_member'):
            self.verify(sig=p.b64(h).encode()+b'..'+sig)

    def test_bad_compact_and_base64_encodings(self):
        protected,_,sig=self.sig.split(b'.')
        cases=[b'',b'..',self.sig+b'\n',protected+b'.payload.'+sig,protected+b'=..'+sig,
               protected+b'..AA',protected+b'..'+sig+b'=',b'a..'+sig,b'\xff..a',self.sig+b'.']
        for value in cases:
            with self.subTest(value=value[:15]), self.assertRaises(p.VerificationError):
                self.verify(sig=value)
        # Signature's final unused base64 bits must be zero.
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
        alternate=alphabet[alphabet.index(chr(sig[-1]))+1].encode()
        with self.assertRaisesRegex(p.VerificationError,'noncanonical_base64url'):
            self.verify(sig=protected+b'..'+sig[:-1]+alternate)

    def test_origin_normalization_and_unsafe_origins(self):
        self.assertEqual(net.normalize_origin('https://CONSUMER-DEMO.example:443/'),PUB)
        for value in ['https://CONSUMER-DEMO.example','https://consumer-demo.example/',
                      'http://consumer-demo.example','https://127.0.0.1','https://user@public.example',
                      'https://public.example?','https://public.example:8443','https://public.example/key']:
            with self.subTest(value=value), self.assertRaises(p.VerificationError):
                p.origin(value)

    def test_good_finding_separates_provenance_applicability_acceptance(self):
        result=self.finding_result()
        self.assertEqual(result['authentication']['state'],'authenticated')
        self.assertEqual(result['applicability'],'matched')
        self.assertEqual(result['acceptance'],'accepted_for_claim')
        self.assertEqual(result['independence'],'unproven')
        self.assertFalse(result['access_granted'])

    def test_unselected_assessor_still_authenticates_but_not_accepted(self):
        result=self.finding_result(trusted=[])
        self.assertEqual(result['authentication']['state'],'authenticated')
        self.assertEqual(result['applicability'],'matched')
        self.assertEqual(result['acceptance'],'unresolved')

    def test_manifest_refresh_invalidates_finding(self):
        result=self.finding_result(manifest=self.manifest+b' ')
        self.assertEqual(result['reason'],'manifest_digest_mismatch')

    def test_wrong_subject_assessor_pointer_typed_claim_and_stale_observation(self):
        changes=[('subject',{'origin':ASS,'type':'platform'}),
                 ('assessor',{'origin':PUB,'relationship':'independent'}),
                 ('claim',{'pointer':'/other','value':True}),
                 ('claim',{'pointer':'/interaction_profile/explicit_invocation_required','value':1}),
                 ('claim',{'pointer':'/interaction_profile/explicit_invocation_required','value':False}),
                 ('expires_at',NOW),('issued_at',NOW+1),
                 ('observation',{'start':0,'end':1791309300}),
                 ('observation',{'start':NOW,'end':NOW}),('observation',{'start':True,'end':NOW}),
                 ('method','unknown'),('limitations',''),('id',PUB+'/findings/x')]
        for field,value in changes:
            f=p.document(self.finding);f[field]=value
            with self.subTest(field=field,value=value):
                result=self.finding_result(f)
                self.assertEqual(result['acceptance'],'unresolved')
                self.assertEqual(result['authentication']['state'],'authenticated')

    def test_correctly_signed_finding_cannot_accept_stale_invalid_or_wrong_issuer_manifest(self):
        import hashlib
        for field, value in [('expires_at', '2026-10-06T18:00:00Z'),
                             ('published_at', '2026-10-06T18:01:00Z'),
                             ('issuer', {'name':'Other', 'uri':ASS, 'domain':'assessor.example'}),
                             ('interaction_profile', None)]:
            manifest=p.document(self.manifest);manifest[field]=value
            m=raw(manifest)
            f=p.document(self.finding);f['manifest_sha256']=hashlib.sha256(m).hexdigest()
            with self.subTest(field=field):
                result=self.finding_result(f,manifest=m)
                self.assertEqual(result['authentication']['state'],'authenticated')
                self.assertEqual(result['acceptance'],'unresolved')

    def test_signature_payload_time_binding(self):
        f=p.document(self.finding);f['issued_at']+=1
        self.assertEqual(self.finding_result(f)['reason'],'finding_time_mismatch')

    def test_publisher_cannot_issue_assessor_statement(self):
        sig=p.sign(self.finding,bytes(range(32)),PUB,p.FINDING,'fictional-1',1791309300,1791313200)
        self.assertEqual(self.finding_result(sig=sig,keys=self.keys)['reason'],'finding_not_authenticated')
        f=p.document(self.finding);f['assessor']['origin']=PUB;f['id']=PUB+'/findings/test'
        payload=raw(f)
        sig=p.sign(payload,bytes(range(32)),PUB,p.FINDING,'fictional-1',1791309300,1791313200)
        result=p.inspect_finding(payload,sig,self.keys,self.manifest,PUB,PUB,[PUB],NOW)
        self.assertEqual(result['authentication']['state'],'authenticated')
        self.assertEqual(result['acceptance'],'unresolved')
        self.assertEqual(result['reason'],'independent_assessor_required')

    def test_finding_list_bound_and_tamper(self):
        self.assertEqual(self.finding_result(trusted=[ASS]*9)['reason'],'too_many_assessors')
        self.assertEqual(self.finding_result(sig=self.fsig[:-2]+b'AA')['acceptance'],'unresolved')

    def test_new_fixture_schemas_and_existing_manifest(self):
        for filename,schema in [('manifest.json','agent-trust-manifest.schema.json'),
                                ('finding.json','invocation-finding-v1.schema.json'),
                                ('publisher.jwks.json','signing-jwks-v1.schema.json'),
                                ('assessor.jwks.json','signing-jwks-v1.schema.json')]:
            self.assertTrue(consume.validate(p.document((FIX/filename).read_bytes()),schema),filename)

    def test_cli_verify_and_wrong_type(self):
        args=[sys.executable,str(ROOT/'tools/signing/cli.py'),'verify','--payload',str(FIX/'manifest.json'),
              '--signature',str(FIX/'manifest.jws'),'--jwks',str(FIX/'publisher.jwks.json'),
              '--origin',PUB,'--type','manifest','--at',str(NOW)]
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)['claims_truth'],'unresolved')
        args[args.index('manifest')]='finding'
        self.assertEqual(subprocess.run(args,capture_output=True).returncode,1)

    def test_cli_sign_exact_vector(self):
        with tempfile.TemporaryDirectory() as d:
            seed=Path(d)/'seed'; seed.write_bytes(bytes(range(32)))
            run=subprocess.run([sys.executable,str(ROOT/'tools/signing/cli.py'),'sign','--payload',
                str(FIX/'manifest.json'),'--seed-file',str(seed),'--origin',PUB,'--type','manifest',
                '--kid','fictional-1','--iat','1791306000','--exp','1791313200'],capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(run.stdout,self.sig)

    def test_consumer_end_to_end_no_access_grant(self):
        run=subprocess.run([sys.executable,str(ROOT/'tools/consumer/consume.py'),'--manifest',str(FIX/'manifest.json'),
            '--expected-origin',PUB,'--at','2026-10-06T18:00:00Z',
            '--status-file',str(ROOT/'examples/consumer/operational-status.json'),
            '--manifest-signature-file',str(FIX/'manifest.jws'),'--manifest-keys-file',str(FIX/'publisher.jwks.json'),
            '--finding-file',str(FIX/'finding.json'),'--finding-signature-file',str(FIX/'finding.jws'),
            '--assessor-keys-file',str(FIX/'assessor.jwks.json'),'--assessor-origin',ASS,'--trusted-assessor',ASS],
            capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        result=json.loads(run.stdout)
        self.assertEqual(result['manifest_authentication']['state'],'authenticated')
        self.assertEqual(result['assessor_finding']['acceptance'],'accepted_for_claim')
        self.assertEqual(result['policy']['decision'],'manual_review')
        self.assertFalse(result['policy']['access_granted'])
        self.assertFalse(result['policy']['approval_granted'])
        self.assertEqual(result['manifest']['authentication'], 'authenticated')
        self.assertNotIn('issuer_authentication_unverified', result['policy']['reasons'])
        self.assertNotIn('claims_not_independently_verified', result['policy']['reasons'])
        pointer = '/interaction_profile/explicit_invocation_required'
        self.assertIn('claim_accepted:' + pointer, result['policy']['reasons'])
        self.assertIn('other_claims_without_accepted_findings', result['policy']['reasons'])
        self.assertIn('operational_status_revocation_not_checked', result['policy']['reasons'])
        self.assertEqual(result['policy']['claim_acceptance'][pointer], 'accepted_for_claim')
        for key, value in result['policy']['claim_acceptance'].items():
            if key != pointer:
                self.assertEqual(value, 'unresolved')
        self.assertEqual(result['assessor_finding']['independence'], 'unproven')

    def consumer_report(self, publisher=True, finding=False, trusted=True, status=True):
        args = ['--manifest', str(FIX/'manifest.json'), '--expected-origin', PUB,
                '--at', '2026-10-06T18:00:00Z']
        if status:
            args += ['--status-file', str(ROOT/'examples/consumer/operational-status.json')]
        if publisher:
            args += ['--manifest-signature-file', str(FIX/'manifest.jws'),
                     '--manifest-keys-file', str(FIX/'publisher.jwks.json')]
        if finding:
            args += ['--finding-file', str(FIX/'finding.json'), '--finding-signature-file', str(FIX/'finding.jws'),
                     '--assessor-keys-file', str(FIX/'assessor.jwks.json'), '--assessor-origin', ASS]
            if trusted:
                args += ['--trusted-assessor', ASS]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = consume.main(args)
        return code, json.loads(output.getvalue())

    def test_publisher_authentication_does_not_accept_any_claim(self):
        code, result = self.consumer_report()
        self.assertEqual(code, 0)
        self.assertNotIn('issuer_authentication_unverified', result['policy']['reasons'])
        self.assertIn('claims_not_independently_verified', result['policy']['reasons'])
        self.assertEqual(set(result['policy']['claim_acceptance'].values()), {'unresolved'})

    def test_unselected_finding_does_not_remove_unresolved_claim_reason(self):
        _, result = self.consumer_report(finding=True, trusted=False)
        self.assertEqual(result['assessor_finding']['authentication']['state'], 'authenticated')
        self.assertEqual(result['assessor_finding']['acceptance'], 'unresolved')
        self.assertIn('claims_not_independently_verified', result['policy']['reasons'])
        self.assertEqual(set(result['policy']['claim_acceptance'].values()), {'unresolved'})

    def test_accepted_finding_cannot_authenticate_its_publisher(self):
        _, result = self.consumer_report(publisher=False, finding=True)
        self.assertEqual(result['assessor_finding']['acceptance'], 'accepted_for_claim')
        self.assertIn('issuer_authentication_unverified', result['policy']['reasons'])
        self.assertEqual(result['manifest']['authentication'], 'unverified')

    def test_claim_acceptance_keeps_other_hold_prerequisites_and_is_idempotent(self):
        code, result = self.consumer_report(finding=True, status=False)
        self.assertEqual(code, 1)
        self.assertEqual(result['policy']['decision'], 'hold')
        self.assertIn('status_file_not_supplied', result['policy']['reasons'])
        self.assertFalse(result['policy']['access_granted'])
        policy = copy.deepcopy(result['policy'])
        consume.reconcile_authentication(result)
        self.assertEqual(result['policy'], policy)

    def test_invalid_publisher_signature_holds_with_specific_reason(self):
        result = consume.inspect(self.manifest, (ROOT/'examples/consumer/operational-status.json').read_bytes(),
                                 PUB, consume.timestamp('2026-10-06T18:00:00Z'))
        result['manifest_authentication'] = p.authenticate(self.manifest + b' ', self.sig, self.keys, PUB, p.MANIFEST, NOW)
        consume.reconcile_authentication(result)
        self.assertEqual(result['manifest_authentication']['state'], 'invalid')
        self.assertEqual(result['manifest']['authentication'], 'invalid')
        self.assertNotIn('issuer_authentication_unverified', result['policy']['reasons'])
        self.assertIn('manifest_signature_invalid:signature_mismatch', result['policy']['reasons'])
        self.assertEqual(result['policy']['decision'], 'hold')
        consume.reconcile_authentication(result)
        self.assertEqual(result['policy']['reasons'].count('manifest_signature_invalid:signature_mismatch'), 1)
        self.assertFalse(result['policy']['access_granted'])

    def test_finding_verifies_once_and_reuses_local_schema_registry(self):
        p.manifest_validator.cache_clear()
        with patch.object(p, 'verify', wraps=p.verify) as verification:
            self.assertEqual(self.finding_result()['acceptance'], 'accepted_for_claim')
            self.assertEqual(verification.call_count, 1)
        with patch.object(Path, 'read_text', side_effect=AssertionError('schema reloaded')):
            self.assertEqual(self.finding_result()['acceptance'], 'accepted_for_claim')

    def test_exported_negative_vector_corpus(self):
        from tools.signing.check_vectors import check
        result = check(FIX)
        self.assertTrue(result['passed'], result['failures'])
        self.assertEqual(result['positive'], 2)
        self.assertEqual(result['negative'], 39)
        self.assertEqual(result['authentication_cases'], 8)

    def test_package_and_direct_entry_points_work_from_other_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            run = subprocess.run([sys.executable, str(ROOT/'tools/signing/cli.py'), 'verify',
                '--payload', str(FIX/'manifest.json'), '--signature', str(FIX/'manifest.jws'),
                '--jwks', str(FIX/'publisher.jwks.json'), '--origin', PUB, '--type', 'manifest', '--at', str(NOW)],
                cwd=directory, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            run = subprocess.run([sys.executable, str(ROOT/'tools/signing/check_vectors.py'), str(FIX)],
                cwd=directory, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            run = subprocess.run([sys.executable, str(ROOT/'tools/consumer/consume.py'),
                '--manifest', str(FIX/'manifest.json'), '--expected-origin', PUB, '--at', '2026-10-06T18:00:00Z'],
                cwd=directory, capture_output=True, text=True)
            self.assertEqual(run.returncode, 1, run.stderr)  # Missing status still holds, but imports work.
            self.assertEqual(json.loads(run.stdout)['manifest']['schema'], 'valid')
            run = subprocess.run([sys.executable, str(ROOT/'tools/consumer/fetch_manifest.py'), 'https://127.0.0.1'],
                cwd=directory, capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(run.stderr.strip(), 'invalid_origin')  # No network request.
            run = subprocess.run([sys.executable, str(ROOT/'tools/consumer/illustrate_protocol_support.py'), '--help'],
                cwd=directory, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
        run = subprocess.run([sys.executable, '-m', 'tools.signing.check_vectors', str(FIX)],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)

    def auth_args(self):
        return Mock(authenticate_manifest=True,manifest_signature_file=None,manifest_keys_file=None,
                    finding_file=None,finding_signature_file=None,assessor_keys_file=None,assessor_origin=None,
                    origin=PUB, max_finding_age_seconds=None)

    def test_network_only_404_is_unsigned_errors_are_unverified(self):
        for error,state in [('signature_absent','unsigned'),('fetch_timeout','unverified'),
                            ('network_failure','unverified'),('http_failure','unverified')]:
            report=consume.base_report()
            with patch.object(consume,'fetch_manifest',side_effect=consume.ConsumerError(error)) as fetch:
                consume.add_authentication(report,self.manifest,PUB,consume.timestamp('2026-10-06T18:00:00Z'),self.auth_args())
                self.assertEqual(report['manifest_authentication']['state'],state)
                self.assertEqual(fetch.call_count,1)

    def test_network_resources_fixed_and_no_report_fetches(self):
        args=self.auth_args(); report=consume.base_report()
        with patch.object(consume,'fetch_manifest',side_effect=[self.sig,self.keys]) as fetch:
            consume.add_authentication(report,self.manifest,PUB,consume.timestamp('2026-10-06T18:00:00Z'),args)
            self.assertEqual([c.args for c in fetch.call_args_list],[(PUB,'signature'),(PUB,'keys')])
        self.assertEqual(report['manifest_authentication']['state'],'authenticated')
        with self.assertRaisesRegex(net.FetchError,'unsupported_resource'):
            net.fetch(PUB,resource='https://evil.example/key')

    def test_fixed_fetch_path_404_encoding_limits_redirects_and_private_dns(self):
        endpoint=(2,1,6,'',('8.8.8.8',443))
        for status,encoding,body,reason in [(404,'identity',b'','signature_absent'),
                (500,'identity',b'','http_failure'),(302,'identity',b'','redirect_rejected'),
                (200,'gzip',b'','unsupported_encoding'),(200,'identity',b'x'*4097,'document_too_large')]:
            response=Mock(status=status)
            response.getheader.side_effect=lambda k,d=None: {'Content-Type':'application/jose','Content-Encoding':encoding}.get(k,d)
            response.getheaders.return_value=[];response.read.return_value=body
            conn=Mock();conn.getresponse.return_value=response
            with self.subTest(status=status,encoding=encoding), self.assertRaisesRegex(net.FetchError,reason):
                net.fetch(PUB,resolver=lambda *a,**k:[endpoint],connection=lambda *a:conn,resource='signature')
            self.assertEqual(conn.request.call_args.args[1],'/.well-known/agent-trust.json.jws')
            conn.close.assert_called_once()
        with self.assertRaisesRegex(net.FetchError,'unsafe_address'):
            net.fetch(PUB,resolver=lambda *a,**k:[(2,1,6,'',('127.0.0.1',443))],resource='keys')


if __name__ == '__main__':
    unittest.main()
