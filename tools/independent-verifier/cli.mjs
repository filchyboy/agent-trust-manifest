// Offline DNS-origin signature verification. Local snapshots require trusted provenance.
import {parseArgs} from 'node:util';
import {openSync, readSync, closeSync} from 'node:fs';
import {verify, Rejection} from './verifier.mjs';
function read(path, limit) {
  let fd;
  try {
    fd = openSync(path, 'r');
    const bytes = Buffer.alloc(limit + 1);
    let length = 0, count;
    while (length < bytes.length && (count = readSync(fd, bytes, length, bytes.length - length, null))) length += count;
    if (length > limit) throw new Rejection('file_too_large');
    return bytes.subarray(0, length);
  } catch (e) { if (e instanceof Rejection) throw e; throw new Rejection('file_unavailable'); }
  finally { if (fd !== undefined) closeSync(fd); }
}
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
    implementation_scope: 'offline-dns-origin-signatures-only', access_granted: false}));
} catch (e) {
  console.error(JSON.stringify({authentication: 'unverified', reason: e instanceof Rejection ? e.message : 'invalid_arguments'}));
  process.exitCode = 1;
}
