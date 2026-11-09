# ATM detached signing profile v1

Status: versioned optional normative profile, `atm-detached-jws/1`. MUST,
MUST NOT and SHOULD have their RFC 2119/RFC 8174 meanings. Reference tools
are optional. This profile authenticates attribution and bytes; it does not
adjudicate claim truth, establish assessor independence, or grant access.

## Wire representation and signing input

Use detached compact JWS ([RFC 7515](https://www.rfc-editor.org/rfc/rfc7515)),
with the unencoded detached payload of
[RFC 7797](https://www.rfc-editor.org/rfc/rfc7797), and only `alg: Ed25519`
([RFC 9864](https://www.rfc-editor.org/rfc/rfc9864)). `EdDSA`, `none`,
other curves/algorithms, attached payloads and JWS JSON serialization MUST
be rejected by this profile. This is JWS, not JWT.

The wire signature is exactly `BASE64URL(protected)..BASE64URL(signature)`
without whitespace or a terminating newline. Base64url MUST be unpadded,
use only the URL alphabet, and round trip to the same encoding (including
unused bits). Signature bytes MUST be 64 bytes. The input to pure Ed25519
is `ASCII(BASE64URL(protected)) || 0x2e || payload_bytes`. No prehash,
canonicalization, parsing/re-serialization, newline stripping, Unicode
normalization, or newline conversion of the payload is permitted. A period
inside a detached payload is allowed. Header member order is unrestricted;
verifiers use the original protected segment, not re-encoded JSON.

Payloads MUST be UTF-8 JSON objects without BOM, duplicate members,
non-finite numbers or unpaired surrogates. All JSON in this profile MUST
be bounded: at most 16 levels below the root, 2048 visited values including
object member names, 128 elements per array, 2048 Unicode characters per
string, and 256 characters per member name. Byte limits are 65536 payload,
4096 compact signature, 2048 decoded protected header, and 16384 JWKS.
These bounds apply even to otherwise valid signatures.

The protected object has exactly these members (unknown members rejected):

| Member | Required value |
| --- | --- |
| `alg` | `Ed25519` |
| `b64` | JSON `false` |
| `crit` | exactly `["b64","atm_profile","origin","iat","exp"]` in this order |
| `atm_profile` | `atm-detached-jws/1` |
| `typ` | `application/atm-manifest+json` or `application/atm-finding+json` |
| `kid` | 1–64 ASCII letters, digits, `_` or `-` |
| `origin` | canonical issuer origin selected independently by the visitor |
| `iat`, `exp` | integer NumericDate seconds, in range 0–253402300799 |

A verifier MUST expect the exact type and origin, require `iat <= now < exp`
and `0 < exp-iat <= 86400`, and reject booleans, strings and fractional
NumericDates. No clock skew is granted. A manifest signature binds publisher
origin; a finding signature binds assessor origin. There are no unprotected
headers or evidence-selected key URLs. `jku`, `x5u` and embedded `jwk` are
not supported. All custom critical parameters MUST be understood.

Canonical origins are ASCII HTTPS origins, lowercase DNS hostname or
compressed public IP literal, no credentials/query/fragment/path/trailing
slash/default `:443`, and no other ports. DNS names need at least two labels,
1–63 ASCII alphanumeric/hyphen characters per label without edge hyphens.
IPv6 literals have brackets. International names require a previously
selected ASCII IDNA form; this profile does not convert Unicode names.
Consumers MAY normalize visitor input (case, `:443`, trailing `/`) before
selecting the expected origin; protected origins MUST already be canonical.
Private, loopback, reserved, multicast, link-local and transition IPs are
not supported by the reference fetcher. Signed JSON never controls origin
selection.

## Publication, HTTP bytes and key binding

A publisher serves the manifest at `/.well-known/agent-trust.json`
(`application/json`), its detached signature at
`/.well-known/agent-trust.json.jws` (`application/jose`), and public JWKS at
`/.well-known/agent-trust-keys.json` (`application/json`), all on the expected
origin using authenticated HTTPS. Media types may have parameters. Requests
use `Accept-Encoding: identity`. This initial profile MUST reject non-identity
Content-Encoding. Payload bytes mean the HTTP message body after transfer
framing removal (e.g. dechunking), with identity content encoding. TLS and
HTTP framing are not signed. Offline files preserve exactly these body bytes.

The key set is a public JWK Set with profile metadata and exactly
`profile`, `origin`, `issued_at`, `expires_at`, `keys`. `profile` is
`atm-detached-jws/1`; `origin` MUST match the independently selected issuer.
`issued_at <= now < expires_at` and `0 < expires_at-issued_at <= 86400` MUST
hold; these are integer NumericDates. It contains 1–16 public entries, each
with exactly `kty: OKP`, `crv: Ed25519`, `alg: Ed25519`, `use: sig`, `kid`,
`x`, `status`, `nbf`, `exp`, plus `retired_at` only for retired keys.
`x` decodes to exactly 32 bytes. IDs are unique across the entire set with
the same grammar as the protected `kid`. Private `d` and other fields are
rejected, including on unused keys. `nbf < exp`, `nbf <= signature.iat < exp`
and `now < exp` are required. An unknown `kid` is unresolved/invalid; it
MUST NOT trigger arbitrary key retrieval.

A freshly supplied key set MUST come from that origin's authenticated HTTPS
channel or an explicit visitor-selected offline snapshot whose provenance
the visitor accepts. Its self-declared `origin` is not proof of provenance.
Offline verification cannot establish that a key set is the latest published
one. The key set is not self-signed; publisher-controlled HTTPS is the initial
binding. Domain control is not a legal identity or reputation claim.

`status` is one of `active`, `retired`, `revoked`, `compromised`. Revoked and
compromised keys MUST be unusable for current assurance regardless of signed
`iat`: a compromised signer can backdate. No historical-validity exception
based only on `iat` is allowed. Trusted independent timestamps and historical
verification are out of scope. Retirement is scheduled rotation, not suspected
compromise: `nbf <= retired_at < exp`, `iat < retired_at <= now` are required.
Previously issued signatures under a retired key can remain valid until
signature/key expiry. A compromise MUST use revoked/compromised, not retirement.

Fresh key snapshots MUST be obtained for each network evaluation; the
reference tool does not persist a cache. Upstream caches MUST NOT serve after
`expires_at` and SHOULD revalidate sooner for compromise response. A key set
may remain apparently usable until its expiry; the 24-hour maximum freshness
window is a real revocation-detection limit, not instantaneous revocation.
Offline snapshots carry the same limitation and can miss intervening updates.
No signed finding-status or finding-revocation feed is implemented.

## Bounded retrieval and deployment

The optional reference consumer fetches at most three fixed same-origin
resources (manifest, signature, keys), with no retries or redirects, no proxies
or credentials, public DNS/IP validation, pinned resolved connection address,
TLS hostname validation, 16 endpoint maximum, 3-second socket timeout, and an
8-second subprocess deadline per request. It rejects ambiguous lengths,
oversize bodies, truncation and non-identity encoding. Discovery URLs inside
manifests/reports are never automatically fetched. Assessor evidence is
explicitly supplied offline. The visitor-selected assessor list has at most
eight entries; no untrusted arbitrary key URL or recursive fetch is permitted.

Only signature HTTP 404 means `unsigned` (confirmed signature absence at
that request). Timeouts, DNS failures, other HTTP statuses, malformed data,
and key lookup failures do not confirm absence; report unverified/invalid.
An absent local signature means not supplied, not a network absence claim.
Missing/invalid signatures MUST NOT confer trust. Authentication status is
separate from schema validity, freshness, applicability and reliance.

Publishers and assessors SHOULD synchronize their clocks and plan a publication
margin between issuing a signed snapshot and first serving it. For example,
signing at time T and serving no earlier than T+60 seconds can accommodate a
verifier up to 60 seconds behind that issuance time, provided every other
not-before/publication timestamp is also valid at the verifier. This is
operational guidance, not a verifier allowance or a guarantee: manifest
`published_at`, JWKS `issued_at`, key `nbf` and finding timestamps also matter.
A later future-dated publication field can still cause rejection. Keep enough
remaining validity for distribution and evaluation; expiry receives no grace.

Use truthful issuance and observation times. Do not mechanically subtract 60
seconds from `iat`: it must remain within the key's validity, and finding
signature `iat` must equal finding `issued_at` and follow observation end.
Do not fabricate observation or publication times to accommodate clock errors.
Publish a correctly timed complete snapshot after synchronization if necessary.

Publishers SHOULD deploy manifest and signature as one atomic release, serve
stable bytes through their CDN, and publish new keys before signing with them.
Keep retired public keys until their final signature expiry. Sequential GETs
may cross releases even with atomic deployment. A digest/signature mismatch
MUST fail that evaluation; clients may evaluate a fresh complete snapshot
later, never combine a favorable signature with different bytes. The reference
consumer does not retry mismatched releases and does not fall back to legacy
embedded signatures. Offline payload/signature/key triples are explicit
snapshots, not evidence of present deployment state.

## Compatibility

Existing ATM core and embedded attestation schemas remain unchanged. Embedded
`attestation` metadata is legacy/unverified unless another explicitly selected
profile authenticates it; fictional signatures in old examples are placeholders.
For migration, preserve useful metadata and publish this detached sidecar over
the complete final manifest bytes, including any embedded legacy metadata.
Do not attempt to compute a signature over a manifest containing that same
signature. Neither deployment-bound nor hardware attestation is implemented.

The [finding profile](finding-profile-v1.md) is additive. Full-manifest digest
binding does not replace `assessed_controls` snapshots in the existing
platform-controls draft, alter normalized rating enums, mandate any provider,
or abolish RFC 0003's authenticated assessor-origin HTTPS publication variant.
