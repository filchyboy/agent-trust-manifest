# Threat Model

ATM addresses the problem of self-asserted trust claims in agent ecosystems.

## Main risks

- false safety declarations
- stale manifests
- signature spoofing
- reputation farming or Sybil attacks
- divergence between declared and observed behavior

## Out of scope

- proving absence of all vulnerabilities
- replacing domain-specific security review

## Detached signing v1 trust boundaries and residual risks

The visitor selects the expected publisher origin, assessor origin, offline
key snapshots and accepted assessors. Manifest/report content cannot select
trust anchors, destinations, executable instructions or authorization policy.
Authenticated HTTPS binds live key publication to the selected origin. Offline
snapshots require separately trusted provenance and may miss newer revocations.
The pinned cryptographic library supplies Ed25519; ATM defines only a
restricted existing JWS profile and claim bindings.

| Attack | Check or limit | Residual boundary |
| --- | --- | --- |
| Altered payload, whitespace or header | Exact raw-byte JWS, protected profile/origin/type/expiry, strict encodings | Authentic bytes can still contain false assertions |
| Algorithm confusion, injected key URLs or private material | Ed25519 only; exact headers; public-only unique-kid JWKS | Compromise of authenticated origin or selected key custody remains possible |
| Backdated signature after compromise | Revoked/compromised keys always unusable regardless of signed iat | A stale snapshot can miss revocation until its expiry; no independent historical timing |
| Planned rotation confused with compromise | Explicit retirement cutoff; compromise never modeled as retirement | Correct publication of key status is issuer's responsibility |
| Replay and stale or future evidence | Signature/key/JWKS windows, observation order, exact manifest digest | Within-window replay is possible; no live deployment proof or nonce |
| JSON/base64 ambiguity or resource exhaustion | Duplicate/invalid scalar rejection, canonical base64url and fixed byte/depth/count limits | Implementation bugs remain possible |
| SSRF, DNS rebinding, redirect or fetch cascade | Fixed endpoints, public-address pinning, TLS, no redirects/proxies, subprocess deadlines | Public-origin availability and the local trust store remain dependencies |
| Publisher substitutes its endorsement for assessor issuance | Separate assessor origin/type/key, subject and typed value comparison | Self-declared independence is not independently established |
| Old/wrong-subject/wrong-value finding attached to refreshed manifest | Full byte digest plus exact subject, pointer and boolean | Deployment, tenant and surface findings are not covered |
| Untrusted or dishonest assessor | Separate authentication, applicability and explicit visitor acceptance | No universal trust adjudication; assessor owns its assessment |
| Finding withdrawn after signing | Short bounded expiry only | No finding status/revocation feed, supersession or transparency log |
| Mixed-release/CDN bytes | Signature mismatch fails evaluation; atomic publication guidance | Availability may suffer during races; no fail-open fallback |

The fictional demonstration contains no genuine observations and no operational
identity. It tests provenance mechanics only. No access grants, tenant removal,
notifications, hardware or deployment attestation are performed. The
[profile](../spec/signing-profile-v1.md) and [finding profile](../spec/finding-profile-v1.md)
state these limitations normatively where applicable.
