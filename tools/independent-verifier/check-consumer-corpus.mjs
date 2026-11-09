import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {inspectFinding} from './finding.mjs';
import {canonicalOrigin} from './origins.mjs';
import {Rejection} from './errors.mjs';
const directory=resolve(process.argv[2] || fileURLToPath(new URL('../../examples/signing/',import.meta.url)));
const corpus=JSON.parse(readFileSync(resolve(directory,'consumer-vectors.json')));
const failures=[];
for (const c of corpus.cases) {
  const s={...corpus.inputs,...c.overrides};
  const read=name => Object.hasOwn(s,name+'_hex') ? Buffer.from(s[name+'_hex'],'hex') : readFileSync(resolve(directory,s[name]));
  const r=inspectFinding(read('finding'),read('signature'),read('jwks'),read('manifest'),s.platform_origin,s.assessor_origin,s.trusted_assessors,s.now,s.max_observation_age);
  const actual={...r,authentication:r.authentication.state,authentication_reason:r.authentication.reason,claims_truth:r.authentication.claims_truth};
  const mismatch=Object.fromEntries(Object.entries(c.expected).filter(([k,v]) => actual[k] !== v).map(([k,v]) => [k,{expected:v,actual:actual[k]}]));
  if (Object.keys(mismatch).length) failures.push({id:c.id,mismatch});
}
const origins=JSON.parse(readFileSync(resolve(directory,'origin-vectors.json'))).cases;
for (const c of origins) {
  let accepted=true;
  try {canonicalOrigin(c.origin);} catch(e) {if (!(e instanceof Rejection)) throw e;accepted=false;}
  if (accepted !== c.accepted) failures.push({origin:c.origin,expected:c.accepted,actual:accepted});
}
console.log(JSON.stringify({implementation:'independent-node-v1',consumer_cases:corpus.cases.length,origin_cases:origins.length,passed:!failures.length,failures}));
process.exitCode=failures.length?1:0;
