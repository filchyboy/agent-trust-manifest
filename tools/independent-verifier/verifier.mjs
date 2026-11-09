// Separate implementation of the v1 signature checks for canonical public origins.
// No Python process, shared production validator, network access, or custom crypto.
import {parseTree} from 'jsonc-parser';
import {createPublicKey, verify as verifySignature} from 'node:crypto';
import {canonicalOrigin} from './origins.mjs';
import {Rejection} from './errors.mjs';
export {Rejection} from './errors.mjs';

function need(test, reason) { if (!test) throw new Rejection(reason); }
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const sameMembers = (v, names) => {
  if (!object(v)) return false;
  const keys = Object.keys(v).sort(), expected = [...names].sort();
  return keys.length === expected.length && keys.every((key, i) => key === expected[i]);
};
const date = v => typeof v === 'number' && Number.isSafeInteger(v) && v >= 0 && v <= 253402300799;
const kidOK = v => typeof v === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(v);

export function strictJSON(bytes, limit = 65536) {
  need(Buffer.isBuffer(bytes) && bytes.length <= limit, 'document_too_large');
  let source;
  try { source = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true}).decode(bytes); }
  catch { throw new Rejection('invalid_json'); }
  need(!source.startsWith('\ufeff'), 'invalid_json');
  let tree;
  const errors = [];
  try { tree = parseTree(source, errors, {disallowComments: true, allowTrailingComma: false, allowEmptyContent: false}); }
  catch { throw new Rejection('overcomplex_json'); }
  if (errors.length) {
    const numberConstant = errors.some(e => /^(?:NaN|Infinity|-Infinity)/.test(source.slice(e.offset)));
    throw new Rejection(numberConstant ? 'invalid_json_number' : 'invalid_json');
  }
  need(tree, 'invalid_json');
  let count = 0;
  const integerMembers = new WeakMap();
  function stringOK(value, maximum = 2048) {
    const chars = [...value];
    need(chars.length <= maximum && chars.every(c => c.codePointAt(0) < 0xd800 || c.codePointAt(0) > 0xdfff), 'invalid_string');
  }
  function walk(node, depth) {
    need(depth <= 16 && ++count <= 2048, 'overcomplex_json');
    if (node.type === 'object') {
      const value = Object.create(null);
      const integers = new Set();
      integerMembers.set(value, integers);
      for (const entry of node.children || []) {
        const [key, item] = entry.children;
        need(!Object.hasOwn(value, key.value), 'duplicate_member');
        need([...key.value].length <= 256, 'overcomplex_json');
        walk(key, depth + 1);
        value[key.value] = walk(item, depth + 1);
        if (item.type === 'number' && /^-?(?:0|[1-9][0-9]*)$/.test(source.slice(item.offset, item.offset + item.length)))
          integers.add(key.value);
      }
      return value;
    }
    if (node.type === 'array') {
      need((node.children || []).length <= 128, 'overcomplex_json');
      return (node.children || []).map(n => walk(n, depth + 1));
    }
    if (node.type === 'number') need(Number.isFinite(node.value), 'invalid_json_number');
    if (node.type === 'string') stringOK(node.value);
    return node.value;
  }
  const value = walk(tree, 0);
  need(object(value), 'object_required');
  return {value, integer: (owner, key) => integerMembers.get(owner)?.has(key) && date(owner[key])};
}

export function decode64(text) {
  need(typeof text === 'string' && /^[A-Za-z0-9_-]+$/.test(text), 'invalid_base64url');
  const bytes = Buffer.from(text, 'base64url');
  need(bytes.toString('base64url') === text, 'noncanonical_base64url');
  return bytes;
}

// Kept as a compatibility alias; public-IP origins are now supported.
export const dnsOrigin = canonicalOrigin;

export function verify(payload, signature, jwks, expectedOrigin, type, now) {
  strictJSON(payload);
  need(Buffer.isBuffer(signature) && signature.length <= 4096, 'invalid_jws');
  need(signature.every(c => c < 128), 'invalid_jws');
  const parts = signature.toString('ascii').split('.');
  need(parts.length === 3, 'invalid_jws');
  const [protected64, detached, sig64] = parts;
  need(detached === '', 'payload_must_be_detached');
  const hd = strictJSON(decode64(protected64), 2048), h = hd.value;
  need(sameMembers(h, ['alg', 'kid', 'typ', 'b64', 'crit', 'atm_profile', 'origin', 'iat', 'exp']), 'unsupported_header');
  need(h.alg === 'Ed25519' && h.b64 === false && h.atm_profile === 'atm-detached-jws/1'
    && JSON.stringify(h.crit) === JSON.stringify(['b64', 'atm_profile', 'origin', 'iat', 'exp']), 'unsupported_profile');
  need(['application/atm-manifest+json', 'application/atm-finding+json'].includes(type) && h.typ === type, 'wrong_type');
  need(canonicalOrigin(h.origin) === canonicalOrigin(expectedOrigin), 'wrong_origin');
  need(kidOK(h.kid), 'invalid_kid');
  need(date(now) && hd.integer(h, 'iat') && hd.integer(h, 'exp') && h.iat <= now && now < h.exp
    && h.exp > h.iat && h.exp - h.iat <= 86400, 'invalid_signature_time');

  const kd = strictJSON(jwks, 16384), ks = kd.value;
  need(sameMembers(ks, ['profile', 'origin', 'issued_at', 'expires_at', 'keys']) && ks.profile === 'atm-detached-jws/1', 'invalid_jwks');
  need(canonicalOrigin(ks.origin) === canonicalOrigin(expectedOrigin), 'wrong_key_origin');
  need(kd.integer(ks, 'issued_at') && kd.integer(ks, 'expires_at') && ks.issued_at <= now && now < ks.expires_at
    && ks.expires_at > ks.issued_at && ks.expires_at - ks.issued_at <= 86400, 'stale_or_invalid_jwks');
  need(Array.isArray(ks.keys) && ks.keys.length >= 1 && ks.keys.length <= 16, 'invalid_keys');
  const keys = new Map();
  for (const k of ks.keys) {
    const required = ['kty', 'crv', 'alg', 'use', 'kid', 'x', 'status', 'nbf', 'exp'];
    need(sameMembers(k, required) || sameMembers(k, [...required, 'retired_at']), 'invalid_public_key');
    need(k.kty === 'OKP' && k.crv === 'Ed25519' && k.alg === 'Ed25519' && k.use === 'sig', 'unsupported_key');
    need(kidOK(k.kid) && !keys.has(k.kid), 'duplicate_or_invalid_kid');
    need(decode64(k.x).length === 32, 'invalid_key_length');
    need(['active', 'retired', 'revoked', 'compromised'].includes(k.status)
      && kd.integer(k, 'nbf') && kd.integer(k, 'exp') && k.nbf < k.exp, 'invalid_key_metadata');
    if (k.status === 'retired') need(kd.integer(k, 'retired_at') && k.nbf <= k.retired_at && k.retired_at < k.exp, 'invalid_retirement');
    else need(!Object.hasOwn(k, 'retired_at'), 'invalid_retirement');
    keys.set(k.kid, k);
  }
  need(keys.has(h.kid), 'unknown_key');
  const k = keys.get(h.kid);
  need(k.status !== 'revoked' && k.status !== 'compromised', 'revoked_key');
  need(k.nbf <= h.iat && h.iat < k.exp && now < k.exp, 'key_time_invalid');
  if (k.status === 'retired') need(h.iat < k.retired_at && k.retired_at <= now, 'retired_key');
  const sig = decode64(sig64);
  need(sig.length === 64, 'invalid_signature_length');
  let valid;
  try {
    const key = createPublicKey({key: {kty: 'OKP', crv: 'Ed25519', x: k.x}, format: 'jwk'});
    valid = verifySignature(null, Buffer.concat([Buffer.from(protected64 + '.', 'ascii'), payload]), key, sig);
  } catch { throw new Rejection('signature_mismatch'); }
  need(valid, 'signature_mismatch');
  return h;
}

// Authentication outcomes are separate from relying-party acceptance and triage.
export function authenticate(payload, signature, jwks, origin, type, now) {
  if (signature === null) return {state:'unverified',reason:'signature_not_supplied'};
  if (jwks === null) return {state:'unverified',reason:'keys_not_supplied'};
  try {
    const h=verify(payload,signature,jwks,origin,type,now);
    return {state:'authenticated',issuer:h.origin,kid:h.kid,expires_at:h.exp,
      reason:'signature_valid',claims_truth:'unresolved'};
  } catch(e) {
    if (!(e instanceof Rejection)) throw e;
    return {state:'invalid',reason:e.message};
  }
}
