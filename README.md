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

Validate an example manifest locally:

```bash
python3 tools/validator/validate.py examples/signed-manifest.json schemas/agent-trust-manifest.schema.json
```

## Implemented validation

The Python CLI accepts a JSON document and a schema path. It parses both files, loads neighboring `*.schema.json` files for reference resolution, and uses `jsonschema` to check the selected schema and validate declared field types, required fields, enums, constants, string lengths and patterns, numeric bounds, object properties, and array items. It reports schema validation failures and returns a nonzero exit code. The workflow runs this CLI against the eight example documents and runs owner-field regression tests.

The CLI does not enforce JSON Schema `format` annotations, including URI and date-time syntax. It does not perform signing, signature verification, hash verification, key generation, expiry enforcement, live interaction checks, or certification. Signing and signature-verification helpers are not implemented in this repository. A successful validation result establishes only the structural constraints checked by this CLI; it does not establish full specification compliance, authenticity, or truthful claims.

## Artifact responsibility

Each `governance_artifacts[].owner` identifies an implementation-defined component or role maintaining that artifact. The field accepts a string containing at least one non-whitespace character. Fictional example labels such as `example_catalog_team` are not a prescribed vocabulary. This field does not identify organization ownership or a verifier and does not grant trust or authority. Earlier accepted nonblank labels remain valid; older validators with a fixed vocabulary may reject new labels. See the core draft specification for details.

Run the owner-field regression tests with `python3 -m unittest discover -s tests`.

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

## Version

Current draft specification: **v0.2.0**. Verification and attestation extension documents retain their v0.1.0 versions. The versioning policy and release checklist are draft project guidance; they do not establish a public governance body or certification program.

## License

Copyright 2026 Christopher Filkins.

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the complete terms and [NOTICE](NOTICE) for attribution.
