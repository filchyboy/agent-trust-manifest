# ATM v0.2.0

This draft release adds typed governance artifact discovery and companion artifact schemas while preserving the small core manifest.

## Scope

- Adds optional `governance_artifacts` discovery to the core manifest schema.
- Adds companion artifact schemas and examples for:
  - `capability_catalog`
  - `revocation_feed`
  - `operational_status_feed`
- Expands the reputation feed schema to support third-party or independent providers, methodology disclosure, flexible scoring/rating/result metadata, evidence references, signatures, assurance, and revocation status.
- Clarifies that first-party operational status belongs in `operational_status_feed`, not in `reputation_feed`.
- Clarifies that richer reputation feeds should be linked as `governance_artifacts` while the legacy `reputation` extension remains a lightweight scorecard pointer.

- Replaces the fixed artifact-owner vocabulary with implementation-defined nonblank strings and clarifies its responsibility role. Examples use fictional vendor-neutral labels.

## Compatibility

This is a backward-compatible minor draft update. Existing v0.1.0 manifests remain valid when they omit `governance_artifacts`. Existing nonblank owner labels remain accepted; older validators with a fixed owner vocabulary may reject newly introduced labels.

## Intent

The release keeps ATM's core declaration small while allowing richer public trust, operational, reputation, revocation, and capability posture to be discovered through hash-pinned companion artifacts.
