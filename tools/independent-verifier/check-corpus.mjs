import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {verify, Rejection} from './verifier.mjs';
const directory = resolve(process.argv[2] || fileURLToPath(new URL('../../examples/signing', import.meta.url)));
const corpus = JSON.parse(readFileSync(resolve(directory, 'vectors.json')));
const bases = new Map(corpus.vectors.map(v => [v.payload, v]));
function inputs(base, o = {}) {
  return [
    o.payload_hex ? Buffer.from(o.payload_hex, 'hex') : readFileSync(resolve(directory, base.payload)),
    o.signature_hex ? Buffer.from(o.signature_hex, 'hex') : readFileSync(resolve(directory, base.signature)),
    o.jwks_hex ? Buffer.from(o.jwks_hex, 'hex') : readFileSync(resolve(directory, base.jwks)),
    o.origin ?? base.origin, o.type ?? base.type, o.now ?? base.now,
  ];
}
for (const v of bases.values()) verify(...inputs(v));
const failures = [];
for (const c of corpus.negative_vectors) {
  let reason = 'unexpected_success';
  try { verify(...inputs(bases.get(c.base_vector), c.overrides)); }
  catch (e) { if (!(e instanceof Rejection)) throw e; reason = e.message; }
  if (reason !== c.expected_reason) failures.push({id: c.id, expected: c.expected_reason, actual: reason});
}
console.log(JSON.stringify({implementation: 'independent-node-dns-v1', positive: bases.size,
  negative: corpus.negative_vectors.length, passed: !failures.length, failures}));
process.exitCode = failures.length ? 1 : 0;
