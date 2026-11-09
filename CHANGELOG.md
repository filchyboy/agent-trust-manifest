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
[runtime security record](docs/python-runtime-security.md) remain linked and
preserved; they document compatibility and security decisions. Merged remote
branches have not been deleted. No release/tag, deployment, notification,
trust-registry integration, or full finding lifecycle is introduced here.
