import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {strictJSON, dnsOrigin, verify, Rejection} from './verifier.mjs';
const fixture = fileURLToPath(new URL('../../examples/signing/', import.meta.url));
const payload = readFileSync(fixture + 'manifest.json');
const signature = readFileSync(fixture + 'manifest.jws');
const keys = readFileSync(fixture + 'publisher.jwks.json');
const origin = 'https://consumer-demo.example';
const kind = 'application/atm-manifest+json', now = 1791309600;
const bytes = v => Buffer.from(JSON.stringify(v));
const rejects = (fn, reason) => assert.throws(fn, e => e instanceof Rejection && e.message === reason);

test('strict JSON refuses extensions, escaped duplicates, bad scalars and invalid UTF-8', () => {
  for (const text of ['{/* comment */"x":1}', '{"x":1,}', '', '{"x":undefined}', '\ufeff{}'])
    rejects(() => strictJSON(Buffer.from(text)), 'invalid_json');
  rejects(() => strictJSON(Buffer.from('{"x":1,"\\u0078":2}')), 'duplicate_member');
  rejects(() => strictJSON(Buffer.from('{"x":1e999}')), 'invalid_json_number');
  rejects(() => strictJSON(Buffer.from('{"x":"\\ud800"}')), 'invalid_string');
  rejects(() => strictJSON(Buffer.from([123, 34, 120, 34, 58, 34, 255, 34, 125])), 'invalid_json');
  rejects(() => strictJSON(bytes([])), 'object_required');
});

test('JSON bounds count Unicode code points, member names, containers and total values', () => {
  strictJSON(bytes({x: '😀'.repeat(2048)}));
  rejects(() => strictJSON(bytes({x: '😀'.repeat(2049)})), 'invalid_string');
  rejects(() => strictJSON(Buffer.from(' '.repeat(65537))), 'document_too_large');
  rejects(() => strictJSON(bytes({x: Array(129).fill(0)})), 'overcomplex_json');
  rejects(() => strictJSON(Buffer.from('{"x":' + '['.repeat(18) + '0' + ']'.repeat(18) + '}')), 'overcomplex_json');
  rejects(() => strictJSON(bytes({['a'.repeat(257)]: 0})), 'overcomplex_json');
  const wide = Object.fromEntries(Array.from({length: 1024}, (_, i) => ['k'+i, 0]));
  rejects(() => strictJSON(bytes(wide)), 'overcomplex_json');
});

test('prototype-looking keys remain data and integer dates retain lexical type', () => {
  const d = strictJSON(Buffer.from('{"__proto__":{"polluted":true},"a":1,"b":1.0,"c":1e0,"d":true,"e":-0}'));
  assert.equal(Object.getPrototypeOf(d.value), null);
  assert.equal({}.polluted, undefined);
  assert(d.integer(d.value, 'a'));
  assert(d.integer(d.value, 'e'));
  assert(!d.integer(d.value, 'b') && !d.integer(d.value, 'c') && !d.integer(d.value, 'd'));
});

test('canonical DNS-only scope fails closed on IP origins and malformed destinations', () => {
  assert.equal(dnsOrigin(origin), origin);
  for (const value of ['https://127.0.0.1', 'https://8.8.8.8', 'https://[2606:4700:4700::1111]'])
    rejects(() => dnsOrigin(value), 'unsupported_ip_origin');
  for (const value of ['http://public.example', 'https://user@public.example', 'https://public.example/key',
    'https://public.example?', 'https://public.example:8443', 'https://localhost'])
    rejects(() => dnsOrigin(value), 'invalid_origin');
  for (const value of [origin+'/', 'https://CONSUMER-DEMO.example', origin+':443'])
    rejects(() => dnsOrigin(value), 'noncanonical_origin');
});

test('retirement is distinct from compromise, and all public key entries are checked', () => {
  const snapshot = JSON.parse(keys);
  snapshot.keys[0].status = 'retired'; snapshot.keys[0].retired_at = now - 1;
  verify(payload, signature, bytes(snapshot), origin, kind, now);
  for (const status of ['revoked', 'compromised']) {
    snapshot.keys[0].status = status; delete snapshot.keys[0].retired_at;
    rejects(() => verify(payload, signature, bytes(snapshot), origin, kind, now), 'revoked_key');
  }
  const unused = JSON.parse(keys);
  unused.keys.push({...unused.keys[0], kid: 'unused', d: 'secret'});
  rejects(() => verify(payload, signature, bytes(unused), origin, kind, now), 'invalid_public_key');
});

test('exact origin, type and unrelaxed expiry are mandatory', () => {
  verify(payload, signature, keys, origin, kind, now);
  rejects(() => verify(payload, signature, keys, origin, 'application/atm-finding+json', now), 'wrong_type');
  rejects(() => verify(payload, signature, keys, 'https://other.example', kind, now), 'wrong_origin');
  rejects(() => verify(payload, signature, keys, origin, kind, 1791313200), 'invalid_signature_time');
});

test('offline CLI authenticates bytes only and fails cleanly on type and file errors', () => {
  const cli = fileURLToPath(new URL('./cli.mjs', import.meta.url));
  const args = [cli, '--payload', fixture+'manifest.json', '--signature', fixture+'manifest.jws',
    '--jwks', fixture+'publisher.jwks.json', '--origin', origin, '--type', 'manifest', '--at', String(now)];
  let run = spawnSync(process.execPath, args, {encoding: 'utf8'});
  assert.equal(run.status, 0, run.stderr);
  const report = JSON.parse(run.stdout);
  assert.equal(report.authentication, 'authenticated');
  assert.equal(report.claims_truth, 'unresolved');
  assert.equal(report.access_granted, false);
  const wrongType = [...args]; wrongType[wrongType.indexOf('manifest')] = 'finding';
  run = spawnSync(process.execPath, wrongType, {encoding: 'utf8'});
  assert.equal(run.status, 1); assert.equal(JSON.parse(run.stderr).reason, 'wrong_type');
  const badFile = [...args]; badFile[badFile.indexOf('--payload')+1] = fixture+'missing';
  run = spawnSync(process.execPath, badFile, {encoding: 'utf8'});
  assert.equal(run.status, 1); assert.equal(JSON.parse(run.stderr).reason, 'file_unavailable');
});
