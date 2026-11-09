# Agent Trust Manifest

ATM is an open draft specification for publisher claims about a receiving
platform's controls and references to supporting assessments. A visiting agent
can discover a claim, authenticate its source under a selected profile, check
what an assessment covers, and choose whether to rely on the assessor.

**Status:** the core schema is **v0.2.0 draft**. `main` also contains unreleased
optional normative signing/finding v1 profiles, experimental companion drafts,
and reference tooling. The [changelog](CHANGELOG.md) distinguishes them; no
v0.3.0 release or tag is implied.

## Responsibility and trust

Publishers own their declarations; assessors own their assessments; visitors
choose which issuers and evidence to trust. A publisher's account of an
assessment is a separate statement from the assessor's own finding.
`verification.verified_by[].report_uri` is discovery, not authenticated issuance.
A visitor can rely on an authenticated, applicable finding from an assessor it
trusts without repeating the assessor's work.

Hashes bind bytes and signatures attribute statements to origin-bound keys.
Neither proves substantive truth, organizational independence, or effective
live controls. Capability discovery, agent ability and operator consent do not
override receiving-platform policy or grant caller permission. The receiving
platform must enforce current conditions at invocation. Missing, stale or
inapplicable evidence remains unresolved.

ATM does not prescribe a universal trust score, provider, PKI, assessment
method or reference executable. Identity/delegation/payment protocols remain
external. See the [verification specification](spec/verification-spec.md),
[ecosystem positioning](docs/ecosystem-positioning.md) and
[related specifications](docs/related-work.md).

## Choose a document or profile

| Need | Contract and status |
| --- | --- |
| Publish declarations | [Core manifest](spec/manifest-spec.md), with the existing v0.2.0 schema |
| Discover assessment and reputation records | [Verification](spec/verification-spec.md) and [reputation](spec/reputation-spec.md) extensions; attribution/applicability still need an authenticated profile |
| Authenticate exact manifest or finding bytes | [Detached signing v1](spec/signing-profile-v1.md), optional normative profile, unreleased |
| Assess explicit invocation | [Invocation finding v1](spec/finding-profile-v1.md), optional full-manifest digest profile for one typed platform claim |
| Describe scoped controls/capability conditions | [Platform-controls 0.1](spec/platform-controls-draft-0.1.md), experimental sidecar/context retaining assessed-controls snapshots |
| Declare external mechanism support | [Protocol-support 0.1](spec/protocol-support-draft-0.1.md), experimental declaration; no adapter or protocol execution |
| Explore business ratings and host lifecycle | [RFC 0002](docs/rfc/0002-third-party-claims-and-host-lifecycle.md), [RFC 0003](docs/rfc/0003-signatory-evidence-profile.md) and [normalization fixtures](examples/rating-normalization/README.md); design/fictional examples, not provider integrations |

The legacy [embedded attestation](spec/attestation-spec.md) schema is preserved.
Its historical placeholder signatures are unverified; the detached profile
provides an explicit migration path. Deployment-bound and hardware attestation
remain broader roadmap work.

## Quick start

Serve the core manifest at `/.well-known/agent-trust.json`. First create the
isolated environment using the [development guide](docs/development.md), including
the pinned Python/pip security bootstrap and project requirements. Then:

```sh
.venv/bin/python tools/validator/validate.py examples/basic-manifest.json schemas/agent-trust-manifest.schema.json
.venv/bin/python tools/validator/validate.py --strict-formats examples/basic-manifest.json schemas/agent-trust-manifest.schema.json
.venv/bin/python -m unittest discover -s tests
.venv/bin/python tools/validator/check_examples.py --strict-formats
```

The validator defaults to structural schema checks. `--strict-formats` adds
supported URI and date-time checks using pinned dependencies; it does not
supply authenticity or current freshness. References resolve locally through
`referencing.Registry`, with unknown references rejected rather than fetched.
Malformed input and schema/reference errors exit 2; invalid documents exit 1;
passed constraints exit 0. Diagnostics identify JSON pointers.

[Validator history](CHANGELOG.md#validator-hardening-record) explains compatibility
limits, including legacy permissions for empty signatures and arbitrary version
strings. Strict mode is recommended explicitly where format checking is wanted;
the default is retained for existing callers. `--structural-only` makes that
choice explicit. CI now checks all 25 distinct catalogued examples in strict
format mode; the old 26-command list repeated one fixture. See the
[conformance matrix](spec/conformance.md) for the limits of each check.

## Run the provenance demonstration

The [signing walkthrough](examples/signing/README.md) supplies a fictional
publisher, fictional assessor, raw-byte signatures and explicit offline key
snapshots. It demonstrates publisher authentication, finding applicability,
and visitor-selected acceptance for the invocation claim as separate results.
The consumer names that one accepted claim and leaves other interaction claims
unresolved. Its original `hold`/`manual_review` triage and false access/approval
outputs remain intact.

```sh
.venv/bin/python tools/signing/check_vectors.py
node tools/signing/interop.mjs
```

The portable corpus contains two valid cases and 39 exact negative inputs with
expected rejection reasons. Python runs the complete corpus; the original Node
harness independently checks the positive signatures and four cryptographic
negative cases. A [separate Node offline consumer](tools/independent-verifier/README.md)
now checks the signature corpus plus 56 shared finding-consumer cases and 159
origin cases, with public-IP origins and independent finding applicability and
visitor acceptance. These checks preserve unresolved truth and independence.

Network manifest authentication is optional and limited to fixed same-origin
manifest/signature/JWKS paths. Generic evidence links are never automatically
followed; assessor findings are supplied offline. Only a signature endpoint's
404 establishes unsigned publication for that request. Key compromise rejects
current assurance regardless of signed issue time. Snapshot and lifecycle
limits are in the [consumer contract](docs/v0.2.0/consumer.md) and
[threat model](docs/threat-model.md).

Every example is fictional and static. Publicly disclosed test seeds must never
be used operationally. Historical dates and method/result labels do not assert
that a live assessment occurred. Schema URLs are locally resolved identifiers;
this repository does not establish hosted availability or domain ownership.

## Documentation and contribution

- [Documentation index](docs/v0.2.0/index.md), [worked status example](docs/v0.2.0/worked-example.md), and [validation chain](docs/v0.2.0/validation-chain.md).
- [Issue #1 decision record](docs/rfc/0001-consumer-policy-resolution.md) and [current review questions](docs/rfc/0001-consumer-policy.md).
- [Verifier evolution brief](docs/rfc/0004-verifier-evolution.md): timing, independent implementation scope and normative/default choices; no v1 rule change.
- [Roadmap](ROADMAP.md), [contributing](CONTRIBUTING.md), [security reporting](SECURITY.md), [versioning](governance/VERSIONING.md), and [release checklist](governance/RELEASE_PROCESS.md).

Repository directories are `spec/`, `schemas/`, `examples/`, `tools/`, `docs/`
and `governance/`. `governance_artifacts[].owner` remains an implementation-defined
maintainer/component label containing non-whitespace text; it is not a verifier
identity or a prescribed vocabulary. Core schemas and normalized-rating enums
retain their compatibility contracts.

Copyright 2026 Christopher Filkins. Licensed under [Apache-2.0](LICENSE); see
[NOTICE](NOTICE) for attribution.
