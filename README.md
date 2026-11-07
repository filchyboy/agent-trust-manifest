# Agent Trust Manifest — v0.2.0 Draft Specification

Agent Trust Manifest (ATM) is an open draft specification for declaring, validating, and progressively strengthening trust signals between software platforms and autonomous agents.

ATM is designed to answer a practical question:

**How can an agent decide whether a system is safe to interact with?**

ATM describes the receiving platform's controls and makes capability conditions discoverable. An agent's ability and operator consent do not authorize a function the platform does not permit. The platform must independently enforce its current policy. Discovery and structural validation grant no caller authority; a listed capability does not guarantee caller eligibility. Missing or stale information remains unresolved, not permission or proof of absence. Agent mandates and delegation protocols remain external.

ATM separates trust into four layers:

1. **Declaration** — machine-readable claims made by a platform.
2. **Verification** — structured evidence that those claims hold.
3. **Reputation** — time-based and observer-based trust signals.
4. **Attestation** — cryptographic proof binding claims to identity and system state.

## Claim → linked validation → visiting-agent verification

ATM gives a visiting agent a path from a platform's claim to a validator's claim about it. The agent can follow that reference, authenticate the validator's statement, check what it covers, and evaluate its evidence under the agent's own policy. A self-asserted platform claim is **eligible for independent validation**; being self-asserted does not make it unverifiable.

The publisher's claim, its description of a validation, and the validator's own finding are separate statements. A `report_uri` is a route to the latter, not an instruction to trust the publisher's summary. The agent must be able to distinguish proof of who made a statement from evidence that its substance is true. A signature or matching domain alone cannot establish control effectiveness, independence, or permission to act.

The third party is responsible for the validity of its own assessment and statement. The visiting agent verifies its authorship (and signature when signed) and applicable bindings, then chooses whether to rely on that third party under its own trust policy. It need not reproduce the assessment to rely on an authenticated, appropriately scoped finding from an assessor it trusts. Publisher endorsement cannot make the third party's statement true, and ATM does not designate universally trusted assessors.

See the [verification extension](spec/verification-spec.md#5-claim-to-validation-discovery) and [worked validation chain](docs/v0.2.0/validation-chain.md). The current schema describes discovery; it does not fully specify an authenticated external-report format. The reference tools check only their documented local constraints and do not follow validation links or verify third-party findings.

## Goals

- Provide a standard location and schema for trust declarations.
- Make trust claims inspectable by agents and software.
- Support progressive assurance rather than binary trust.
- Keep the base manifest small while allowing extension sets.
- Avoid forcing a single trust engine or policy model.

## Non-goals

- Defining one universal trust score.
- Replacing application security reviews.
- Mandating one reputation provider or PKI model.
- Embedding proprietary policy logic into the standard.

## Repository layout

- `spec/` — draft specification documents
- `schemas/` — JSON Schemas for manifest and extensions
- `examples/` — example manifests and reports
- `tools/validator/` — JSON schema validation CLI
- `docs/` — lifecycle, threat model, and design notes
- `governance/` — proposed versioning policy and release checklist

## Quick start

Example manifest location:

```text
/.well-known/agent-trust.json
```

Create an isolated Python environment and install the validator dependency:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install jsonschema
```

Validate an example manifest using that environment:

```bash
.venv/bin/python tools/validator/validate.py examples/signed-manifest.json schemas/agent-trust-manifest.schema.json
```

## Implemented validation

The supplied validator and reference consumer are optional tools. Independent implementations can consume and verify ATM documents without using either; conformance concerns the applicable schemas and specification semantics, not a particular executable.

The Python CLI accepts a JSON document and a schema path. It parses both files, loads neighboring `*.schema.json` files for reference resolution, and uses `jsonschema` to check the selected schema and validate declared field types, required fields, enums, constants, string lengths and patterns, numeric bounds, object properties, and array items. It reports schema validation failures and returns a nonzero exit code. The workflow runs this CLI against the example documents and runs the regression tests.

The CLI does not enforce JSON Schema `format` annotations, including URI and date-time syntax. It does not perform signing, signature verification, hash verification, key generation, expiry enforcement, live interaction checks, or certification. Signing and signature-verification helpers are not implemented in this repository. A successful validation result establishes only the structural constraints checked by this CLI; it does not establish full specification compliance, authenticity, or truthful claims.

## Reference consumer and versioned documentation

A small post-prerelease reference consumer inventories declarations and evidence, checks the exact bytes of an explicitly supplied operational-status file, and reports freshness and failure states. Its illustrative policy returns `hold` or `manual_review`; neither grants access or proves trust. Evidence is never automatically fetched, and publisher authentication and independent assessment remain unverified.

Start with the [v0.2.0 documentation index](docs/v0.2.0/index.md), [worked fictional example](docs/v0.2.0/worked-example.md), and [consumer contract](docs/v0.2.0/consumer.md). The [focused RFC questions](docs/rfc/0001-consumer-policy.md) cover scope, minimum evidence, freshness, failure handling and issuer trust. These additions are not in the original tagged prerelease archives.

## Unreleased platform-control profile

A [separately versioned experimental profile](spec/platform-controls-draft-0.1.md) distinguishes publisher, platform subject/deployment/surface, control authority, enforcement point and assessor. It uses the existing `platform_policy` discovery link and explicit offline sidecar/context inputs. Its fixtures test capability conditions, subject type, exact evidence applicability, policy changes and approval requirements while always granting no access. The v0.2.0 schema contracts remain unchanged; this proposal is not a new release. See [unreleased notes](spec/platform-controls-draft-notes.md). [Issue #1](https://github.com/filchyboy/agent-trust-manifest/issues/1) remains the design record; draft PR #2 remains a bounded consumer testbed.

## Declaring external protocol support

The separate [protocol-support draft 0.1](spec/protocol-support-draft-0.1.md) lets platform or tenant administrators declare external mechanisms for one exact platform/deployment/tenant/surface/capability context. It records protocol/specification identifiers, explicit versions and profiles, supported/unsupported/unknown status, endpoint/documentation references, and optional support versus required alternatives or joint requirements. This is separate from a capability's transport (`fulfillment.protocol`), `auth.context`, and free-text conditions.

Configuration can publish these declarations; it does not install an adapter, enable runtime access, verify interoperability or grant caller authority. An external mechanism such as Visa TAP can be named by its reviewed specification/revision; the [fixtures](examples/consumer/protocol-support/declaration.json) use fictional mechanisms and claim no integration. The original schemas and platform-control draft remain unchanged. A [separate offline illustration](docs/protocol-support-consumers.md) shows possible consumer handling without implementing protocols, fetching providers or enforcing platform policy.

## Artifact responsibility

Each `governance_artifacts[].owner` identifies an implementation-defined component or role maintaining that artifact. The field accepts a string containing at least one non-whitespace character. Fictional example labels such as `example_catalog_team` are not a prescribed vocabulary. This field does not identify organization ownership or a verifier and does not grant trust or authority. Earlier accepted nonblank labels remain valid; older validators with a fixed vocabulary may reject new labels. See the core draft specification for details.

Run the regression tests with `.venv/bin/python -m unittest discover -s tests`.

## Example limitations

All files under `examples/` are fictional, static fixtures. Their historical dates, scores, verification results, deployment identifiers, signatures, and hashes do not establish live freshness, certification, successful cryptographic verification, or production readiness. Placeholder signatures and hashes must be replaced and verified before operational use. The minimal validator checks schema structure; it does not verify signatures, hashes, current expiry, or live platform behavior. Schema identifiers under `agenttrustmanifest.org` are identifiers in this draft; hosted availability and domain control are not established here.

## Specification set

- Core manifest: `spec/manifest-spec.md`
- Verification extension: `spec/verification-spec.md`
- Reputation extension: `spec/reputation-spec.md`
- Attestation extension: `spec/attestation-spec.md`

Draft companion artifact schemas:

- Capability catalog: `schemas/capability-catalog.schema.json`
- Operational status feed: `schemas/operational-status-feed.schema.json`
- Revocation feed: `schemas/revocation-feed.schema.json`
- Release notes and scope: `spec/release-notes-v0.2.0.md`

## How ATM fits with other agent trust efforts

ATM focuses on portable receiving-platform declarations, capability prerequisites and evidence about controls. Identity, user authorization, platform permission and control effectiveness are separate questions. Related efforts span several of them; they do not fit exclusive agent/platform buckets.

| Related work | Function and relationship to ATM |
| --- | --- |
| [Cloudflare recognition system](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/) (historically signed agents) | Requester recognition and classification that already inform receiving-side traffic rules. ATM could describe surrounding platform controls and evidence. |
| [Visa Trusted Agent Protocol](https://developer.visa.com/docs/trusted-agent-protocol/trusted-agent-protocol-specifications) | Commerce recognition and consumer/payment signals that merchants can use to admit or limit interactions. |
| [AP2 v0.2](https://ap2-protocol.org/ap2/specification/) | Checkout/Payment Mandates and verification responsibilities across commerce participants; transaction authorization complements platform-control declarations. |
| [Verifiable Intent](https://verifiableintent.dev/spec/) | An open draft for cryptographic delegation and transaction evidence, distinct from the Mastercard Agent Pay product; not blanket merchant permission. |
| [Signature Agent Card](https://www.ietf.org/archive/id/draft-meunier-webbotauth-registry-03.txt) | Individual Internet-Draft coauthored by Thibault Meunier for requester metadata and keys; declared behavior does not establish receiving-platform controls. |
| [Agent Identity Document](https://www.ietf.org/archive/id/draft-alla-agent-identity-document-01.txt) | Femi Alla's individual Internet-Draft for hosted identity/accountability, separating provider facts from operator assertions. |

Cloudflare and TAP already support receiving-side policy decisions. ATM does not replace their enforcement, identity discovery, delegation or payment mechanisms. A listed capability does not guarantee caller eligibility; operator consent and agent ability cannot override platform refusal or required additional approval.

See the [ecosystem analysis](docs/ecosystem-positioning.md) for control subjects, enforcement locations, overlap, an illustrative interaction and primary-source dates/versions. AP2 v0.2 differs from its launch terminology; the identity drafts and VI are work in progress. ATM's local platform-control profile is draft and unpublished. No compatibility with these efforts has been implemented or tested; references imply no certification, endorsement or partnership.

[Proposed roadmap](ROADMAP.md).

## Version

Current draft specification: **v0.2.0**. Verification and attestation extension documents retain their v0.1.0 versions. The versioning policy and release checklist are draft project guidance; they do not establish a public governance body or certification program.

## License

Copyright 2026 Christopher Filkins.

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the complete terms and [NOTICE](NOTICE) for attribution.
