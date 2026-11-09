// Independent offline classification using a versioned public-address policy snapshot.
import {readFileSync} from 'node:fs';
import {isIP} from 'node:net';
import {Rejection} from './errors.mjs';
const policy = JSON.parse(readFileSync(new URL('./ip-policy-v1.json', import.meta.url)));
const need = (value, reason) => { if (!value) throw new Rejection(reason); };
function bits(host) {
  const family = isIP(host);
  if (family === 4) return {width: 32, value: host.split('.').reduce((a, n) => (a << 8n) | BigInt(n), 0n)};
  need(family === 6, 'invalid_origin');
  // URL/isIP supply the validated syntax; this only encodes the native canonical result.
  const canonical = new URL('https://[' + host + ']').hostname.slice(1, -1);
  const sides = canonical.split('::');
  const left = sides[0] ? sides[0].split(':') : [];
  const right = sides.length > 1 && sides[1] ? sides[1].split(':') : [];
  const words = sides.length === 1 ? left : [...left, ...Array(8-left.length-right.length).fill('0'), ...right];
  return {width: 128, value: words.reduce((a, n) => (a << 16n) | BigInt('0x'+n), 0n)};
}
const ranges = Object.fromEntries(['ipv4','ipv6'].map(family => [family,
  Object.fromEntries(Object.entries(policy[family]).map(([name, entries]) => [name, entries.map(cidr => {
    const [host, prefix] = cidr.split('/'), address = bits(host);
    const shift = BigInt(address.width - Number(prefix));
    return {width: address.width, shift, network: address.value >> shift};
  })]))]));
export function publicAddress(host) {
  if (!isIP(host)) return false;
  const address = bits(host), family = address.width === 32 ? 'ipv4' : 'ipv6';
  const matches = name => ranges[family][name].some(r => (address.value >> r.shift) === r.network);
  return !matches('always_reject') && (!matches('private') || matches('private_exceptions'));
}
export function canonicalOrigin(value) {
  need(typeof value === 'string' && value.length <= 256 && /^[\x21-\x7e]+$/.test(value), 'invalid_origin');
  let url;
  try { url = new URL(value); } catch { throw new Rejection('invalid_origin'); }
  need(url.protocol === 'https:' && !url.username && !url.password && !url.port
    && url.pathname === '/' && !/[?#%\\]/.test(value), 'invalid_origin');
  const host = url.hostname.replace(/^\[|\]$/g, '');
  if (isIP(host)) need(publicAddress(host), 'invalid_origin');
  else {
    const labels = host.split('.');
    need(labels.length >= 2 && host.length <= 253 && labels.every(v => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(v))
      && !/^[0-9.]+$/.test(host), 'invalid_origin');
  }
  need('https://' + url.hostname === value, 'noncanonical_origin');
  return value;
}
