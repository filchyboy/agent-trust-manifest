# Changelog

## Unreleased

- Clarify release status, current signature-failure handling and offline
  interoperability coverage in the README and signing rollout notes. These
  editorial corrections follow the immutable v0.3.0 snapshot; they do not
  change protocol rules or runtime behavior.

## v0.3.0 — tagged snapshot; GitHub release draft

The tag identifies commit `2867bd876c63304474d51368fe4ce6430c343a3c`, including
PR #13. As of 2026-11-09 its GitHub release is an unpublished draft prerelease.
The entries below describe changes since the published v0.2.0 baseline included
in that snapshot. Project version v0.3.0 does not change core `atm_version: 0.2.0`,
`atm-detached-jws/1` or `atm-invocation-finding/1`. Later changes appear under
Unreleased above; the tag is not moved to include them.

| Area | Status and boundary |
| --- | --- |
| Core manifest and legacy verification/attestation schemas | Existing draft contracts, preserved for compatibility |
| `atm-detached-jws/1` and `atm-invocation-finding/1` | Optional normative profiles with reference code and reproducible vectors in the tagged snapshot |
| Platform-controls and protocol-support 0.1 | Experimental companion drafts, not part of the original release contract |
| Consumer | Optional bounded reference demonstration; publisher authentication and one claim's visitor-selected acceptance are separate from access decisions |
| Rating normalization and host lifecycle proposals | Fictional normalization fixtures and design guidance; no provider integration or automated host lifecycle |

### Publisher authentication failure handling

- Invalid requested manifest authentication now forces `hold`, exit 1 and
  `manifest_signature_invalid:<reason>`, preserving other hold reasons and
  independently reported assessor-claim acceptance. A valid finding cannot
  clear this publisher-authentication hold.
- Not requested, confirmed signature HTTP 404 (`unsigned`), and unavailable
  authentication material (`unverified`) remain distinct. Those outcomes retain
  existing triage behavior; manual review and exit 0 never establish authentication.
- Rename the ambiguous `revocation_not_checked` policy reason to
  `operational_status_revocation_not_checked`. It describes operational-status
  evidence, not the signing-key checks or finding withdrawal. Callers consuming
  reason codes must update to the new spelling.
- Add eight shared offline authentication outcomes for Python and Node, including
  a changed manifest value. Policy-level CLI tests separately cover hold/exit
  behavior, unavailable inputs and accepted findings alongside invalid signatures.
- Document synchronized clocks and publication margins without changing v1's
  time rules.

### Offline consumers and conformance

- Add an independent offline Node finding consumer and bounded CLI. Both
  implementations check 56 shared acceptance/applicability cases and 159 origin
  cases; Node now handles public IPv4/IPv6 literals and retains the existing
  two-positive/39-negative signature corpus.
- Add an optional visitor-selected maximum observation age to both consumers.
  It only tightens acceptance; authenticated applicability is separate. Preserve
  v1 expiry, 24-hour limits, zero skew and revoked-key handling. Boundary cases
  cover exact expiry, 24-hour limits and future issuance at 59/60/61 seconds.
- Explicitly select strict formats for all 25 distinct CI authoring examples,
  preserving the structural CLI default and adding `--structural-only` for
  explicit callers. Remove one duplicate fixture invocation from the former
  26-command workflow through a curated local catalogue.
- Restate existing core conformance requirements using BCP 14 words and publish
  a class/check matrix. No core schema assertions, required fields, enums or
  legacy placeholder permissions change; no truth or access guarantee is added.

The unresolved product decision is a new audit/timing profile: actual control
snapshot, acceptable observation age/replay horizon, status/withdrawal evidence
and consistent clock allowance. No universal long lifetime or v2 default is
invented. Independent organizational review, network conformance, finding
status/revocation and deployment-bound evidence remain outside this change.

### Reporting and vector coverage

- Reconcile successful publisher authentication with the consumer's reason
  codes. Report an accepted finding for its exact claim, while other interaction
  claims remain unresolved. Access and approval outputs remain false.
- Export 39 exact negative JWS inputs and expected rejection reasons alongside
  the two positive vectors. Run the whole corpus with the reference Python
  verifier; independently reject four cryptographic tamper cases with Node.
  The original primitive-only harness did not cover full profile parsing or
  finding acceptance; the offline consumers described above add that coverage.
- Authenticate a finding once, cache the local schema registry per process,
  and use package imports with shared offline origin validation. Preserve direct
  CLI entry points and bounded fetch behavior.

### Additional changes in the snapshot

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

### Compatibility records

The useful existing specification notes and
[runtime security record](docs/development.md#historical-remediation-record) remain linked and
preserved; they document compatibility and security decisions. Finding lifecycle
and trust-registry integration remain outside the implemented profiles.

### Initial independent-verifier and documentation follow-up (historical)

At that stage, a separate DNS-origin Node prototype checked the two positive and all 39
negative signing vectors without invoking Python. Seven additional Node test
groups cover strict parsing, lexical date types, retirement, CLI behavior and
origin limits. That initial prototype was offline, rejected IP origins, and did not implement
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
