# Changelog

## Unreleased

This section describes work on `main` after the v0.2.0 draft baseline; it does
not announce a new release or tag. Core schemas retain their existing versions.

| Area | Status and boundary |
| --- | --- |
| Core manifest and legacy verification/attestation schemas | Existing draft contracts, preserved for compatibility |
| `atm-detached-jws/1` and `atm-invocation-finding/1` | Optional normative profiles with reference code and reproducible vectors; unreleased |
| Platform-controls and protocol-support 0.1 | Experimental companion drafts, not part of the original release contract |
| Consumer | Optional bounded reference demonstration; publisher authentication and one claim's visitor-selected acceptance are separate from access decisions |
| Rating normalization and host lifecycle proposals | Fictional normalization fixtures and design guidance; no provider integration or automated host lifecycle |

### Reporting and vector follow-up

- Reconcile successful publisher authentication with the consumer's reason
  codes. Report an accepted finding for its exact claim, while other interaction
  claims remain unresolved. Preserve hold/manual-review decisions and false
  access/approval outputs.
- Export 39 exact negative JWS inputs and expected rejection reasons alongside
  the two positive vectors. Run the whole corpus with the reference Python
  verifier; independently reject four cryptographic tamper cases with Node.
  A complete second hostile-input profile implementation remains outstanding.
- Authenticate a finding once, cache the local schema registry per process,
  and use package imports with shared offline origin validation. Preserve direct
  CLI entry points and bounded fetch behavior.

### Existing unreleased additions

- [Detached signing and assessor pilot](docs/signing-v1-release-notes.md):
  exact-byte Ed25519 JWS, origin/type/expiry bindings, same-origin public JWKS,
  explicit offline assessor inputs, compromise/retirement distinctions, and
  a fictional invocation finding.
- [Validator hardening](spec/validator-hardening-notes.md): local
  `referencing.Registry`, strict JSON input handling, stable exit codes and
  sorted JSON-pointer diagnostics. Structural validation remains the default;
  `--strict-formats` remains an explicit compatibility-preserving option.
- [Claim-to-validation clarification](spec/validation-chain-clarification-notes.md):
  publisher discovery assertions, assessor responsibility, visitor-selected
  reliance and the distinction between authenticity and truth.
- [Platform controls](spec/platform-controls-draft-notes.md) and
  [protocol-support declarations](spec/protocol-support-draft-notes.md):
  scoped experimental artifacts and offline illustrations, preserving existing
  core enums and assessed-controls snapshots.

### Time-policy decisions preserved

The current v1 profile deliberately caps JWKS freshness, signature lifetime,
and the finding observation-to-expiry interval at 24 hours and allows no clock
skew. These are documented profile rules, not parsing bugs. This follow-up does
not silently relax them or change the structural validator's default.

The operational cost for long-lived audit reports is real. A later profile
revision should distinguish report validity, observation age and visitor-selected
maximum age, define all clock comparisons consistently (manifest, JWKS, key,
signature and finding), and account for the missing finding-revocation/status
mechanism. Fetching a key set on each evaluation does not eliminate upstream
caching or offline-snapshot revocation limits. A daily signing schedule does
not require exporting a key from hardware or putting it in the application
runtime. Accurate clocks and a planned publication margin are deployment
requirements of the current profile; observation timestamps must not be
fabricated to work around clock differences.

### Release and maintenance boundaries

The useful existing specification notes and
[runtime security record](docs/development.md#historical-remediation-record) remain linked and
preserved; they document compatibility and security decisions. Merged remote
branches have not been deleted. No release/tag, deployment, notification,
trust-registry integration, or full finding lifecycle is introduced here.

### Local independent-verifier and documentation follow-up

A separate DNS-origin Node prototype now checks the two positive and all 39
negative signing vectors without invoking Python. Seven additional Node test
groups cover strict parsing, lexical date types, retirement, CLI behavior and
origin limits. It remains offline, rejects IP origins, and does not implement
finding applicability or relying-party acceptance. This is progress toward a
second implementation, not completion of the independent-consumer milestone.

[Verifier evolution decision brief](docs/rfc/0004-verifier-evolution.md) analyzes
long-lived audits, coherent clock tolerance, strict-format defaults and older
normative wording. It changes none of the v1 time limits or conformance rules.

## Historical compatibility records

The following records preserve the detailed text formerly held in specification
note files. Statements about draft PRs, local-only work and publication state
refer to the time each record was written, not current branch or CI status.
Current profile and implementation status is summarized above.

### Validator hardening record

The optional CLI now uses a local `referencing.Registry` rather than deprecated `RefResolver`. Its default retains structural validation without format enforcement. An explicit `--strict-formats` mode checks formats using pinned URI and RFC3339 dependencies. Existing valid examples retain their meaning; no JSON Schema assertions, required fields, enums or core version contracts change.

The CLI supports the repository's Draft 2020-12 schemas. References resolve only from neighboring `*.schema.json` files; unknown references fail, with no network retrieval. Duplicate object keys and nonfinite JSON constants are rejected rather than silently normalized. Errors are sorted by JSON pointer then message; root errors use `<root>`. Exit codes: 0 checked constraints passed, 1 document validation failed, 2 input/schema/dependency/reference error. Scripts should use exit codes rather than depend on the previous `VALID:` display prefix.

Strict formats are not full ATM conformance, authentication, current freshness, signature verification, hash comparison, safe URL retrieval or truth checking. In particular, legacy schema permissions for arbitrary version/algorithm strings, empty signatures/hashes and empty verification arrays remain. Tightening these contracts requires an explicit compatibility decision, not a hidden CLI change. The consumer's bounded semantic rules remain separate.

Regression tests cover both modes, URI/date-time failures, invalid dates, missing fields, wrong types, malformed JSON, duplicate keys, nonfinite constants, invalid UTF-8, missing files, bad schemas and unresolved references. They also explicitly preserve the boundary that format-valid documents can contain unauthenticated or insufficient declarations.

### Validation-chain clarification record

This clarification makes the existing intended flow explicit: a publisher states a claim, supplies a link to a validator's claim about it, and a visiting agent can follow that link to verify provenance and evaluate applicability and substance.

- Adds field-level schema descriptions separating publisher summaries from authenticated assessor statements.
- Expands verification and core guidance, including safe retrieval and precise result presentation.
- Makes third-party signatory responsibility and visitor-selected trust explicit: authenticated, scoped findings may be relied on without repeating the assessment; publisher endorsement does not establish their truth.
- States that the supplied validator and reference consumer are optional, not mandated implementations.
- Adds an offline worked chain with a manifest, a fictional outside finding, and reproducible exact-byte manifest binding.
- Explains the existing report schema's optional fields and incomplete authentication/applicability bindings without claiming those mechanisms are implemented.

No JSON Schema assertions, required fields, enum values, document shapes, release tags or runtime consumer behavior change. The external finding is an illustrative report, not a newly standardized format. A future normative verification profile would need separate review and versioning.

#### Detailed third-party and lifecycle proposal

Adds design guidance for tenant/claim bindings, open provider ecosystems, normalized provider-native ratings, host withdrawal and tenant notification, conflict handling, outages, expiry and restoration. Includes a fictional normalized reputation-feed fixture and consistency checks using the existing enums. No new schema fields or enum values are introduced; raw source formats remain provider-specific. Host lifecycle operations and cryptographic verification are design work, not implemented capabilities.

### Platform-controls draft record

- Preserve all v0.2.0 schema bytes and existing example contracts; introduce separately versioned experimental sidecar/context schemas compatible with ATM 0.2.0.
- Discover explicit platform roles, scope/deployment/policy and capability prerequisites through the existing `platform_policy` artifact mechanism. Keep agent mandates external and caller eligibility unresolved.
- Add a positive fixture and explicit negative mutation fixtures for issue #1; check schema, digest, subject type, exact applicability and freshness independently.
- Advance the bounded consumer report to `atm-consumer-demo/0.2`, adding unresolved platform-control/caller states and rejecting agent-typed platform status evidence. Both decisions continue to grant no access or approval.
- Keep issue #1 open as the design decision record and draft PR #2 as an existing bounded testbed. These local changes do not edit either GitHub resource or publish any version.

Focused local review fixes: bind each assessment to the exact declared authority, enforcement point and capability-condition snapshot, and preserve inspected manifest/status states when requested sidecar/context input fails. Both remain declaration-only checks.

### Protocol-support draft record

- Add a separately versioned declaration companion compatible with ATM 0.2.0. Preserve the original seven schemas, the existing platform-control/context schemas and all published consumer behavior.
- Declare exact protocol/specification/version/profile tuples, scoped support status, distinct endpoint/documentation references, and optional support versus one-of/all-of requirement groups for one concrete platform/tenant/deployment/surface/capability/policy binding.
- Keep administrator configuration, protocol adapters, actual caller eligibility, independently tested support and runtime authorization distinct. No inheritance, protocol implementation, certification or access grants are added.
- Add generic fictional positive/negative fixtures, structural-validation tests and a separately labelled non-normative offline illustration. Its vocabulary/triage choices do not define mandatory ATM policy.
- Migration requires publishing a new companion/version, not inserting fields into older closed profiles or reusing old evidence as support for new claims. No release, commit, push, PR update or issue closure is part of this local addition.
