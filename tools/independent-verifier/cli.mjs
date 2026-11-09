// Offline v1 signature verification. Local snapshots require trusted provenance.
import {parseArgs} from 'node:util';
import {readLocal as read} from './io.mjs';
import {verify, Rejection} from './verifier.mjs';

try {
  const {values} = parseArgs({options: Object.fromEntries(
    ['payload', 'signature', 'jwks', 'origin', 'type', 'at'].map(k => [k, {type: 'string'}])), strict: true});
  if (!['payload', 'signature', 'jwks', 'origin', 'type'].every(k => values[k])
    || !['manifest', 'finding'].includes(values.type)) throw new Rejection('invalid_arguments');
  if (values.at !== undefined && !/^(?:0|[1-9][0-9]*)$/.test(values.at)) throw new Rejection('invalid_decision_time');
  const now = values.at === undefined ? Math.floor(Date.now() / 1000) : Number(values.at);
  const h = verify(read(values.payload, 65536), read(values.signature, 4096), read(values.jwks, 16384),
    values.origin, values.type === 'manifest' ? 'application/atm-manifest+json' : 'application/atm-finding+json', now);
  console.log(JSON.stringify({authentication: 'authenticated', issuer: h.origin, claims_truth: 'unresolved',
    implementation_scope: 'offline-v1-signatures-only', access_granted: false}));
} catch (e) {
  console.error(JSON.stringify({authentication: 'unverified', reason: e instanceof Rejection ? e.message : 'invalid_arguments'}));
  process.exitCode = 1;
}
