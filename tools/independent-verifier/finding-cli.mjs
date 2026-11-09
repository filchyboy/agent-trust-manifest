// Visitor-selected offline finding evaluation; no network or access decision.
import {parseArgs} from 'node:util';
import {readLocal} from './io.mjs';
import {inspectFinding} from './finding.mjs';
import {Rejection} from './errors.mjs';
import {verify} from './verifier.mjs';
try {
  const options=Object.fromEntries(['finding','signature','jwks','manifest','platform-origin','assessor-origin','manifest-signature','manifest-jwks','at','max-finding-age-seconds'].map(k=>[k,{type:'string'}]));
  options['trusted-assessor']={type:'string',multiple:true,default:[]};
  const {values:v}=parseArgs({options,strict:true});
  if (!['finding','signature','jwks','manifest','platform-origin','assessor-origin'].every(k=>v[k])) throw new Rejection('invalid_arguments');
  for (const field of ['at','max-finding-age-seconds'])
    if (v[field]!==undefined && !/^-?(?:0|[1-9][0-9]*)$/.test(v[field])) throw new Rejection('invalid_arguments');
  const now=v.at===undefined?Math.floor(Date.now()/1000):Number(v.at);
  const maximum=v['max-finding-age-seconds']===undefined?null:Number(v['max-finding-age-seconds']);
  const manifest=readLocal(v.manifest,65536);
  const result=inspectFinding(readLocal(v.finding,65536),readLocal(v.signature,4096),readLocal(v.jwks,16384),
    manifest,v['platform-origin'],v['assessor-origin'],v['trusted-assessor'],now,maximum);
  const publisherRequested=Boolean(v['manifest-signature'] || v['manifest-jwks']);
  result.manifest_authentication={state:'unverified',reason:'not_requested'};
  if (publisherRequested) {
    try {
      if (!v['manifest-signature'] || !v['manifest-jwks']) throw new Rejection('manifest_signature_and_keys_required');
      const h=verify(manifest,readLocal(v['manifest-signature'],4096),readLocal(v['manifest-jwks'],16384),
        v['platform-origin'],'application/atm-manifest+json',now);
      result.manifest_authentication={state:'authenticated',issuer:h.origin,kid:h.kid,reason:'signature_valid',claims_truth:'unresolved'};
    } catch(e) {
      if (!(e instanceof Rejection)) throw e;
      const inputError=['file_unavailable','file_too_large','manifest_signature_and_keys_required'].includes(e.message);
      result.manifest_authentication={state:inputError?'unverified':'invalid',reason:e.message};
    }
  }
  console.log(JSON.stringify(result));
  process.exitCode=result.acceptance==='accepted_for_claim' && (!publisherRequested || result.manifest_authentication.state==='authenticated')?0:1;
} catch(e) {
  console.error(JSON.stringify({authentication:{state:'unverified'},applicability:'unresolved',acceptance:'unresolved',
    access_granted:false,reason:e instanceof Rejection?e.message:'invalid_arguments'}));
  process.exitCode=1;
}
