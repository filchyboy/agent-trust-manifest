# Unreleased clarification: claim-to-validation discovery

This clarification makes the existing intended flow explicit: a publisher states a claim, supplies a link to a validator's claim about it, and a visiting agent can follow that link to verify provenance and evaluate applicability and substance.

- Adds field-level schema descriptions separating publisher summaries from authenticated assessor statements.
- Expands verification and core guidance, including safe retrieval and precise result presentation.
- Adds an offline worked chain with a manifest, a fictional outside finding, and reproducible exact-byte manifest binding.
- Explains the existing report schema's optional fields and incomplete authentication/applicability bindings without claiming those mechanisms are implemented.

No JSON Schema assertions, required fields, enum values, document shapes, release tags or runtime consumer behavior change. The external finding is an illustrative report, not a newly standardized format. A future normative verification profile would need separate review and versioning.
