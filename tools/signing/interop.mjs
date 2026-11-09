// Independent Node crypto signing-input implementation for the shared vectors.
// This is a vector interoperability check, not a general untrusted-input verifier.
import {readFileSync} from 'node:fs';
import {createPublicKey, createPrivateKey, verify, sign, createHash} from 'node:crypto';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const dir = resolve(process.argv[2] || 'examples/signing');
const vectors = JSON.parse(readFileSync(resolve(dir, 'vectors.json'))).vectors;
const results = [];
for (const v of vectors) {
  const payload = readFileSync(resolve(dir, v.payload));
  const [protected64, detached, signature64] = readFileSync(resolve(dir, v.signature), 'ascii').split('.');
  assert.equal(detached, '');
  const h = JSON.parse(Buffer.from(protected64, 'base64url'));
  assert.equal(h.alg, 'Ed25519');
  assert.equal(h.b64, false);
  assert.equal(h.typ, v.type);
  assert.equal(h.origin, v.origin);
  assert.deepEqual(h.crit, ['b64', 'atm_profile', 'origin', 'iat', 'exp']);
  assert.equal(h.atm_profile, 'atm-detached-jws/1');
  assert(h.iat <= v.now && v.now < h.exp);
  const key = JSON.parse(readFileSync(resolve(dir, v.jwks))).keys.find(k => k.kid === h.kid);
  const publicKey = createPublicKey({key: {kty: key.kty, crv: key.crv, x: key.x}, format: 'jwk'});
  const input = Buffer.concat([Buffer.from(protected64 + '.', 'ascii'), payload]);
  assert.equal(input.toString('hex'), v.signing_input_hex);
  assert.equal(createHash('sha256').update(payload).digest('hex'), v.payload_sha256);
  const sig = Buffer.from(signature64, 'base64url');
  assert(verify(null, input, publicKey, sig));
  assert(!verify(null, Buffer.concat([input, Buffer.from(' ')]), publicKey, sig));
  // Independently sign with Node; Python tests verify this output too.
  const seed = Buffer.from(v.fictional_private_seed_hex, 'hex');
  const pkcs8 = Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'), seed]);
  const privateKey = createPrivateKey({key: pkcs8, format: 'der', type: 'pkcs8'});
  const reverse = sign(null, input, privateKey);
  assert.deepEqual(reverse, sig);
  results.push({payload: v.payload, verified: true, tamper_rejected: true,
    node_jws: protected64 + '..' + reverse.toString('base64url')});
}
console.log(JSON.stringify(results));
