# Agent Trust Manifest Draft Specification v0.2.0

## 1. Overview

The Agent Trust Manifest (ATM) is a JSON document published by a system operator to declare machine-readable trust properties for agent interaction.

The default well-known location is:

```text
/.well-known/agent-trust.json
```

## 2. Design goals

The core manifest should:

- be easy to fetch and parse
- support partial trust rather than binary trust
- separate declaration from proof
- remain stable even as verification and attestation evolve

## 3. Required top-level fields

### `atm_version`
String. The ATM core spec version implemented by the document.

### `manifest_version`
String. The publisher's version for this manifest instance.

### `issuer`
Object describing the publishing entity.

Required subfields:
- `name`
- `uri`
- `domain`

### `published_at`
RFC 3339 timestamp.

### `expires_at`
RFC 3339 timestamp.

### `interaction_profile`
Object declaring the platform's interaction constraints.

Required subfields:
- `content_triggered_execution`
- `explicit_invocation_required`
- `provenance_available`
- `audit_logging_available`

## 4. Optional extension fields

The following fields are optional in the core spec but standardized in companion specs:

- `verification`
- `reputation`
- `attestation`
- `governance_artifacts`

### `governance_artifacts`

Array of hash-pinned companion artifacts that describe public governance state outside the small core manifest.

Initial artifact types:

- `capability_catalog`
- `platform_policy`
- `api_catalog`
- `evaluation_status`
- `provenance_manifest`
- `ui_governance`
- `compliance_manifest`
- `operational_status_feed`
- `reputation_feed`
- `revocation_feed`

Each entry identifies the artifact `type`, `uri`, `schema_uri`, `version`, `owner`, `hash`, `last_updated`, `assurance_level`, `scope`, `issuer`, and `subject`.

#### Artifact `owner`

`governance_artifacts[].owner` is an implementation-defined string identifying the responsible component or role maintaining the referenced artifact. It must contain at least one non-whitespace character. For example, fictional implementations might use `example_catalog_team` or `example_ratings_team`; these labels are illustrative, not a required or recommended vocabulary.

This field does not identify the owner of an organization or a verifier, establish verifier independence, or grant trust or authority. It does not replace the separate `issuer`, `subject`, or verification identity fields.

This draft widens the earlier fixed owner vocabulary to accept any nonblank string while retaining the existing field name and artifact shape. Previously accepted owner labels remain valid. Validators using the earlier fixed vocabulary may reject new implementation-defined labels until their schema is updated.

Companion artifacts should not expose private implementation details such as internal policy rule IDs, internal TOON bindings, tenant identifiers, raw evidence payloads, secrets, or private guardrail configuration.

The legacy `reputation` extension remains a lightweight pointer to an external scorecard. New implementations that need hash pinning, issuer/subject responsibility, freshness metadata, acceptance controls, or multiple companion artifacts should use `governance_artifacts` entries of type `reputation_feed`.

## 5. Core semantics

### `content_triggered_execution`
Boolean. Indicates whether content alone can trigger a consequential action without an explicit user or policy-approved invocation.

### `explicit_invocation_required`
Boolean. Indicates whether consequential actions require an explicit invocation boundary.

### `provenance_available`
Boolean. Indicates whether returned outputs can carry source or lineage metadata.

### `audit_logging_available`
Boolean. Indicates whether the platform can record decision and execution artifacts for later inspection.

## 6. Security considerations

A core ATM document is a declaration, not proof. Consumers should treat unsigned or unverified manifests as low-assurance claims.

## 7. Conformance

A manifest conforms to ATM v0.2.0 if:

- it validates against the JSON schema
- required fields are present
- timestamps are syntactically valid
- extension sections, if present, conform to their extension specs

The reference CLI checks structural schema constraints only. It does not enforce URI or timestamp formats, verify signatures or hashes, or establish the truth of declared claims. Passing the CLI alone does not demonstrate all of the conformance requirements above or establish authenticity.
