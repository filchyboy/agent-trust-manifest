# Optional detached provenance v1: rollout and current status

As of 2026-11-09, the implementation described here is included in project tag
`v0.3.0` at `2867bd876c63304474d51368fe4ce6430c343a3c`. The corresponding GitHub
release is an unpublished draft prerelease. Core `atm_version` remains `0.2.0`;
`atm-detached-jws/1` and `atm-invocation-finding/1` retain their identifiers and
v1 timing rules. Subsequent editorial corrections do not change the tag.

Four scoped additions implement an optional provenance pilot:

1. Normative `atm-detached-jws/1` and `atm-invocation-finding/1` profiles,
   public key/finding schemas, and deterministic exact-byte shared vectors.
2. Restricted offline Ed25519 detached JWS signing/verification CLI using
   pinned PyCA cryptography; independent Node crypto verification and reciprocal
   signing checks. No new cryptographic primitive or canonicalization scheme.
3. Additive consumer authentication status, fixed same-origin bounded optional
   signature/JWKS retrieval, and explicit trusted offline snapshots. Only a
   signature endpoint's HTTP 404 establishes unsigned publication for that request.
4. One fictional assessor finding about explicit invocation, with origin, typed
   value, full-manifest digest and observation/expiry binding, plus separate
   visitor-selected acceptance. Publisher endorsement cannot issue assessor evidence.

Revoked/compromised keys are rejected regardless of signed `iat`; planned
retirement is distinct. Cache/offline freshness and deployment race limits are
explicit. Existing core schemas, enum normalization, assessed-controls scoped
snapshots, default structural validator and `--strict-formats` remain intact.
RFC 0003's authenticated-origin publication variant remains available.
Legacy embedded attestation retains useful metadata and schema compatibility.

The pilot does not prove substantive truth or independence, perform live tests,
supply a universal assessor list, implement finding status/revocation feeds,
transparency or deployment attestation, grant access, remove tenants, or send
notifications. No provider partnership or business-rating integration is claimed.
See [instructions and vectors](../examples/signing/README.md) and
[threat model](threat-model.md).

## Follow-up reporting and interoperability fixes

Publisher authentication now clears its stale unverified-issuer explanation.
An accepted finding is named and reported per claim; other interaction claims
remain unresolved. Nested manifest authentication agrees with the separate
provenance result. Invalid requested publisher authentication now forces
`hold`, exit 1 and `manifest_signature_invalid:<reason>`, preserving other hold
reasons. A separately accepted assessor finding cannot clear this hold.
Signature HTTP 404 is `unsigned`; unavailable material remains `unverified`.
Those outcomes retain existing triage behavior, so `manual_review` and exit 0
are not authentication-success flags. Access and approval remain false.

The renamed `operational_status_revocation_not_checked` reason describes
operational-status evidence withdrawal. Key status is checked against the
supplied current-window JWKS, subject to snapshot freshness limits. Finding
withdrawal/status remains a separate unimplemented capability.

The Python and separate Node offline implementations both check two positive
and 39 negative signature vectors, eight authentication outcomes, 56 finding
cases and 159 origin cases. The original Node primitive harness separately
checks reciprocal deterministic signing and four cryptographic tamper cases.
Node's offline consumer does not implement HTTP retrieval or Python's
operational-status triage policy. Both implementations were developed within
this project; no external organizational assessment or independent third-party
implementation is claimed.

Python signing and consumer modules use a shared origin package, findings
authenticate once, and local manifest schemas are cached per process. The
[conformance matrix](../spec/conformance.md) identifies each implementation's
scope. See [CHANGELOG](../CHANGELOG.md) for snapshot history, subsequent changes
and the retained 24-hour/zero-skew v1 time policy.
