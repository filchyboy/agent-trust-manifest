# Agent Trust Manifest — v0.2.0 Draft Specification

Agent Trust Manifest (ATM) is an open draft specification for declaring, validating, and progressively strengthening trust signals between software platforms and autonomous agents.

ATM is designed to answer a practical question:

**How can an agent decide whether a system is safe to interact with?**

ATM separates trust into four layers:

1. **Declaration** — machine-readable claims made by a platform.
2. **Verification** — structured evidence that those claims hold.
3. **Reputation** — time-based and observer-based trust signals.
4. **Attestation** — cryptographic proof binding claims to identity and system state.

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

The Python CLI accepts a JSON document and a schema path. It parses both files, loads neighboring `*.schema.json` files for reference resolution, and uses `jsonschema` to check the selected schema and validate declared field types, required fields, enums, constants, string lengths and patterns, numeric bounds, object properties, and array items. It reports schema validation failures and returns a nonzero exit code. The workflow runs this CLI against the example documents and runs the regression tests.

The CLI does not enforce JSON Schema `format` annotations, including URI and date-time syntax. It does not perform signing, signature verification, hash verification, key generation, expiry enforcement, live interaction checks, or certification. Signing and signature-verification helpers are not implemented in this repository. A successful validation result establishes only the structural constraints checked by this CLI; it does not establish full specification compliance, authenticity, or truthful claims.

## Reference consumer and versioned documentation

A small post-prerelease reference consumer inventories declarations and evidence, checks the exact bytes of an explicitly supplied operational-status file, and reports freshness and failure states. Its illustrative policy returns `hold` or `manual_review`; neither grants access or proves trust. Evidence is never automatically fetched, and publisher authentication and independent assessment remain unverified.

Start with the [v0.2.0 documentation index](docs/v0.2.0/index.md), [worked fictional example](docs/v0.2.0/worked-example.md), and [consumer contract](docs/v0.2.0/consumer.md). The [focused RFC questions](docs/rfc/0001-consumer-policy.md) cover scope, minimum evidence, freshness, failure handling and issuer trust. These additions are not in the original tagged prerelease archives.

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

ATM proposes a portable way to describe a system’s agent-interaction controls and connect those claims to independently assessable evidence.

An agent interaction raises four separate questions:

1. Identity: Who is making the request?
2. User authorization: What did the user authorize?
3. Platform permission: Does the receiving platform permit this interaction?
4. Controls and evidence: What safeguards does the system claim, and what supports those claims?

ATM focuses on the fourth question. Its integration work should preserve the distinctions between all four. Recognizing an agent’s identity does not grant it access, and permission for a transaction does not establish that the surrounding system’s controls are effective.

Related efforts include:

- [Cloudflare signed agents](https://blog.cloudflare.com/signed-agents/): signed HTTP requests that help identify agent traffic
- [Visa Trusted Agent Protocol](https://developer.visa.com/capabilities/trusted-agent-protocol): signals that help merchants recognize approved commerce agents and associated authorization
- [Google Agent Payments Protocol](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol): signed mandates supporting user authorization and accountability in payments
- [Mastercard Verifiable Intent](https://www.mastercard.com/us/en/news-and-trends/stories/2026/verifiable-intent.html): evidence linking user authorization to agent actions

ATM is intended to complement these mechanisms with evidence about system controls. It grants no access rights and does not replace identity, authorization or payment protocols.

These are potential integration points. ATM v0.2.0 supplies schemas and structural validation; compatibility with these efforts has not been implemented or tested. References imply no certification, endorsement or partnership.

[Proposed roadmap](ROADMAP.md).

## Version

Current draft specification: **v0.2.0**. Verification and attestation extension documents retain their v0.1.0 versions. The versioning policy and release checklist are draft project guidance; they do not establish a public governance body or certification program.

## License

Copyright 2026 Christopher Filkins.

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the complete terms and [NOTICE](NOTICE) for attribution.
