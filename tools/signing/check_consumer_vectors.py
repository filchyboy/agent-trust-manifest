"""Run shared offline finding/origin cases with the Python reference implementation."""
import json
from pathlib import Path
import sys
if __package__ in (None,''): sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.signing import atm_signing as p


def check(directory):
    corpus=json.loads((directory/'consumer-vectors.json').read_bytes());base=corpus['inputs']
    results=[]
    for case in corpus['cases']:
        settings={**base,**case['overrides']}
        def read(name):
            return bytes.fromhex(settings[name+'_hex']) if name+'_hex' in settings else (directory/settings[name]).read_bytes()
        report=p.inspect_finding(read('finding'),read('signature'),read('jwks'),read('manifest'),settings['platform_origin'],
            settings['assessor_origin'],settings['trusted_assessors'],settings['now'],settings['max_observation_age'])
        actual={**report,'authentication':report['authentication']['state'],'authentication_reason':report['authentication']['reason'],
                'claims_truth':report['authentication'].get('claims_truth')}
        mismatch={k:{'expected':v,'actual':actual.get(k)} for k,v in case['expected'].items() if actual.get(k)!=v}
        if mismatch: results.append({'id':case['id'],'mismatch':mismatch})
    origins=json.loads((directory/'origin-vectors.json').read_bytes())['cases']
    for case in origins:
        try: p.origin(case['origin']);accepted=True
        except p.VerificationError: accepted=False
        if accepted != case['accepted']: results.append({'origin':case['origin'],'actual':accepted})
    return {'consumer_cases':len(corpus['cases']),'origin_cases':len(origins),'passed':not results,'failures':results}


if __name__=='__main__':
    result=check(Path(__file__).resolve().parents[2]/'examples/signing')
    print(json.dumps(result));raise SystemExit(0 if result['passed'] else 1)
