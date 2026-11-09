# Unreleased clarification: claim-to-validation discovery

This clarification makes the existing intended flow explicit: a publisher states a claim, supplies a link to a validator's claim about it, and a visiting agent can follow that link to verify provenance and evaluate applicability and substance.

- Adds field-level schema descriptions separating publisher summaries from authenticated assessor statements.
- Expands verification and core guidance, including safe retrieval and precise result presentation.
- Makes third-party signatory responsibility and visitor-selected trust explicit: authenticated, scoped findings may be relied on without repeating the assessment; publisher endorsement does not establish their truth.
- States that the supplied validator and reference consumer are optional, not mandated implementations.
- Adds an offline worked chain with a manifest, a fictional outside finding, and reproducible exact-byte manifest binding.
- Explains the existing report schema's optional fields and incomplete authentication/applicability bindings without claiming those mechanisms are implemented.

No JSON Schema assertions, required fields, enum values, document shapes, release tags or runtime consumer behavior change. The external finding is an illustrative report, not a newly standardized format. A future normative verification profile would need separate review and versioning.

## Detailed third-party and lifecycle proposal

Adds design guidance for tenant/claim bindings, open provider ecosystems, normalized provider-native ratings, host withdrawal and tenant notification, conflict handling, outages, expiry and restoration. Includes a fictional normalized reputation-feed fixture and consistency checks using the existing enums. No new schema fields or enum values are introduced; raw source formats remain provider-specific. Host lifecycle operations and cryptographic verification are design work, not implemented capabilities.
