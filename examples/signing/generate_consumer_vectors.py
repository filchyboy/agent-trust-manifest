"""Generate portable fictional finding and origin cases; never contact fixture origins."""
import copy
import hashlib
import ipaddress
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.signing import atm_signing as p

HERE=Path(__file__).resolve().parent
PUB='https://consumer-demo.example'
ASS='https://assessor.example'
NOW=1791309600
IAT=1791309300
EXP=1791313200


def encoded(value):
    return (json.dumps(value,indent=2)+'\n').encode()


def generate():
    manifest=(HERE/'manifest.json').read_bytes()
    finding=json.loads((HERE/'finding.json').read_bytes())
    keys=json.loads((HERE/'assessor.jwks.json').read_bytes())
    cases=[]

    def add(name, reason='visitor_selected_assessor', applicability='matched', acceptance='accepted_for_claim',
            authentication='authenticated', f=None, m=None, issuer=ASS, k=None, overrides=None, auth_reason=None):
        o=dict(overrides or {})
        if m is not None:
            o['manifest_hex']=encoded(m).hex()
            f=copy.deepcopy(finding if f is None else f)
            f['manifest_sha256']=hashlib.sha256(bytes.fromhex(o['manifest_hex'])).hexdigest()
        if f is not None:
            body=encoded(f)
            o['finding_hex']=body.hex()
            o['signature_hex']=p.sign(body,bytes(range(32)) if issuer==PUB else bytes(range(32,64)),
                                      issuer,p.FINDING,'fictional-1',IAT,EXP).hex()
        if k is not None: o['jwks_hex']=encoded(k).hex()
        expected={'authentication':authentication,'applicability':applicability,'acceptance':acceptance,
                  'reason':reason,'access_granted':False}
        if applicability=='matched': expected['independence']='unproven'
        if auth_reason: expected['authentication_reason']=auth_reason
        if authentication=='authenticated': expected['claims_truth']='unresolved'
        cases.append({'id':name,'overrides':o,'expected':expected})

    add('selected-assessor-supportive-claim')
    add('assessor-not-selected','assessor_not_selected',acceptance='unresolved',overrides={'trusted_assessors':[]})
    for relation in ['affiliated','self']:
        f=copy.deepcopy(finding);f['assessor']['relationship']=relation
        add(relation+'-relationship','independent_assessor_required',acceptance='unresolved',f=f)
    f=copy.deepcopy(finding);f['assessor']['origin']=PUB;f['id']=PUB+'/findings/self-assessment'
    add('publisher-self-assessment','independent_assessor_required',acceptance='unresolved',f=f,issuer=PUB,
        overrides={'assessor_origin':PUB,'trusted_assessors':[PUB],
                   'jwks_hex':(HERE/'publisher.jwks.json').read_bytes().hex()})
    add('publisher-cannot-issue-assessor-finding','finding_not_authenticated','unresolved','unresolved','invalid',
        f=finding,issuer=PUB,k=json.loads((HERE/'publisher.jwks.json').read_bytes()),auth_reason='wrong_origin')
    mutations=[
        ('wrong-platform-subject','subject',{'origin':ASS,'type':'platform'},'wrong_subject'),
        ('agent-is-not-platform','subject',{'origin':PUB,'type':'agent'},'wrong_subject'),
        ('wrong-assessor','assessor',{'origin':PUB,'relationship':'independent'},'assessor_mismatch'),
        ('wrong-claim-pointer','claim',{'pointer':'/other','value':True},'invalid_typed_claim'),
        ('integer-is-not-boolean','claim',{'pointer':finding['claim']['pointer'],'value':1},'invalid_typed_claim'),
        ('wrong-asserted-boolean','claim',{'pointer':finding['claim']['pointer'],'value':False},'claim_value_mismatch'),
        ('expired-finding','expires_at',NOW,'invalid_finding_time'),
        ('future-finding','issued_at',NOW+1,'invalid_finding_time'),
        ('wrong-signature-time-binding','issued_at',IAT+1,'finding_time_mismatch'),
        ('reversed-observation','observation',{'start':IAT,'end':IAT-1},'invalid_finding_time'),
        ('overlong-observation-window','observation',{'start':EXP-86401,'end':IAT},'invalid_finding_time'),
        ('float-observation-date','observation',{'start':float(IAT-10),'end':IAT},'invalid_finding_time'),
        ('boolean-observation-date','observation',{'start':True,'end':IAT},'invalid_finding_time'),
        ('wrong-finding-profile','profile','unknown','unsupported_finding'),
        ('foreign-finding-id','id',PUB+'/findings/test','invalid_finding_id'),
        ('empty-limitations','limitations','','invalid_finding_metadata'),
    ]
    for name,field,value,reason in mutations:
        f=copy.deepcopy(finding);f[field]=value
        add(name,reason,'unresolved','unresolved',f=f)
    add('manifest-refresh-invalidates-binding','manifest_digest_mismatch','unresolved','unresolved',
        overrides={'manifest_hex':(manifest+b' ').hex()})
    add('finding-byte-tamper','finding_not_authenticated','unresolved','unresolved','invalid',
        overrides={'finding_hex':((HERE/'finding.json').read_bytes()+b' ').hex()},auth_reason='signature_mismatch')
    for name,field,value,reason in [
        ('stale-manifest','expires_at','2026-10-06T18:00:00Z','stale_or_future_manifest'),
        ('future-manifest','published_at','2026-10-06T18:00:00.000001Z','stale_or_future_manifest'),
        ('invalid-calendar-date','published_at','2026-02-30T17:00:00Z','invalid_manifest_time'),
        ('wrong-manifest-issuer','issuer',{'name':'Other','uri':ASS,'domain':'assessor.example'},'manifest_subject_mismatch'),
        ('invalid-manifest-schema','interaction_profile',None,'invalid_manifest_schema'),
    ]:
        m=json.loads(manifest);m[field]=value
        add(name,reason,'unresolved','unresolved',m=m)
    for state in ['revoked','compromised']:
        k=copy.deepcopy(keys);k['keys'][0]['status']=state
        add('assessor-key-'+state,'finding_not_authenticated','unresolved','unresolved','invalid',k=k,auth_reason='revoked_key')
    for result in ['fail','unknown']:
        f=copy.deepcopy(finding);f['result']=result
        add('assessor-result-'+result,'finding_not_supportive',acceptance='unresolved',f=f)
    add('visitor-age-inclusive-boundary',overrides={'max_observation_age':NOW-IAT})
    add('visitor-age-too-old','finding_observation_too_old',acceptance='unresolved',overrides={'max_observation_age':NOW-IAT-1})
    add('invalid-visitor-age-policy','invalid_observation_age_policy','unresolved','unresolved',overrides={'max_observation_age':True})
    add('bounded-assessor-list','too_many_assessors','unresolved','unresolved',overrides={'trusted_assessors':[ASS]*9})
    add('exact-issuance-now',overrides={'now':IAT,'max_observation_age':0})
    for offset in [59,60,61]:
        add('no-future-grace-'+str(offset),'finding_not_authenticated','unresolved','unresolved','invalid',
            overrides={'now':IAT-offset},auth_reason='invalid_signature_time')
    add('one-second-before-expiry',overrides={'now':EXP-1})
    for offset in [0,1]:
        add('expiry-boundary-plus-'+str(offset),'finding_not_authenticated','unresolved','unresolved','invalid',
            overrides={'now':EXP+offset},auth_reason='invalid_signature_time')
    f=copy.deepcopy(finding);f['observation']['start']=EXP-86400
    add('observation-window-exact-24-hours',f=f)
    k=copy.deepcopy(keys);k['issued_at']=EXP-86400
    add('key-snapshot-exact-24-hours',k=k)
    k['issued_at']-=1
    add('key-snapshot-over-24-hours','finding_not_authenticated','unresolved','unresolved','invalid',k=k,
        auth_reason='stale_or_invalid_jwks')
    for name,field,value,reason in [
        ('maximum-calendar-fraction','expires_at','9999-12-31T23:59:59.999999Z',None),
        ('minimum-calendar-fraction','published_at','0001-01-01T00:00:00.000001Z',None),
        ('utc-underflow','published_at','0001-01-01T00:00:00+01:00','invalid_manifest_time'),
        ('utc-overflow','expires_at','9999-12-31T23:59:59-01:00','invalid_manifest_time'),
        ('valid-offset-publication','published_at','2026-10-06T10:00:00-07:00',None),
        ('unknown-utc-offset','published_at','2026-10-06T17:00:00-00:00','invalid_manifest_time'),
        ('valid-leap-calendar','published_at','2024-02-29T17:00:00Z',None),
    ]:
        m=json.loads(manifest);m[field]=value
        if reason: add(name,reason,'unresolved','unresolved',m=m)
        else: add(name,m=m)
    for platform in ['https://8.8.8.8','https://[2606:4700:4700::1111]']:
        m=json.loads(manifest);m['issuer']['uri']=platform
        m['issuer']['domain']=platform.split('//',1)[1].strip('[]')
        f=copy.deepcopy(finding);f['subject']['origin']=platform
        add('public-ip-platform-'+('v6' if '[' in platform else 'v4'),f=f,m=m,overrides={'platform_origin':platform})
    inputs={'manifest':'manifest.json','finding':'finding.json','signature':'finding.jws','jwks':'assessor.jwks.json',
            'platform_origin':PUB,'assessor_origin':ASS,'trusted_assessors':[ASS],'now':NOW,'max_observation_age':None}
    (HERE/'consumer-vectors.json').write_bytes(encoded({'profile':'atm-offline-consumer-cases/1','warning':'Fictional statements and public test keys; no real assessment, IP ownership or independence proof. No requests are made to address literals.',
                                                       'inputs':inputs,'cases':cases}))
    policy=json.loads((HERE.parents[1]/'tools/independent-verifier/ip-policy-v1.json').read_bytes())
    origins={PUB,'https://CONSUMER-DEMO.example','https://consumer-demo.example/','http://consumer-demo.example',
             'https://consumer-demo.example:443','https://consumer-demo.example/key','https://consumer-demo.example?',
             'https://user@consumer-demo.example','https://localhost','https://8.8.8.8','https://[2606:4700:4700::1111]'}
    for family in ['ipv4','ipv6']:
        for entries in policy[family].values():
            for cidr in entries:
                network=ipaddress.ip_network(cidr);limit=2**network.max_prefixlen
                for n in [int(network.network_address)-1,int(network.network_address),int(network.broadcast_address),int(network.broadcast_address)+1]:
                    if not 0<=n<limit: continue
                    address=type(network.network_address)(n)
                    origins.add('https://'+('['+str(address)+']' if address.version==6 else str(address)))
    origin_cases=[]
    for value in sorted(origins):
        try: p.origin(value); accepted=True
        except p.VerificationError: accepted=False
        origin_cases.append({'origin':value,'accepted':accepted})
    (HERE/'origin-vectors.json').write_bytes(encoded({'profile':'atm-origin-cases/1',
        'source':policy['source'],'warning':'Address syntax/classification only; no requests or real issuer-ownership claims.', 'cases':origin_cases}))
    print(json.dumps({'consumer_cases':len(cases),'origin_cases':len(origin_cases)}))


if __name__=='__main__': generate()
