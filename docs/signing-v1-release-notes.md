# Unreleased: optional detached provenance v1

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
provenance result. Triage decisions, operational-status evidence requirements,
and access/approval behavior are unchanged.

The portable corpus now includes 39 explicit negative inputs and expected
rejections. Node independently rejects the four cryptographic tamper cases;
Python executes the full corpus. Signing and consumer modules use a shared
origin package, findings authenticate once, and local manifest schemas are
cached per process. See [CHANGELOG](../CHANGELOG.md) for unreleased status and
the time-policy decisions preserved by this follow-up.
