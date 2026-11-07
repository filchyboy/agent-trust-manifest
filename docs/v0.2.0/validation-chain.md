# Worked example: follow the validation claim, then evaluate it

[Documentation index](index.md) · [Verification specification](../../spec/verification-spec.md#5-claim-to-validation-discovery)

ATM's intended flow is **platform claim → link to a validator's claim → visiting agent verifies and evaluates that claim**. The publisher is not asked to prove its own trustworthiness merely by writing a `pass` field. A self-asserted control can be independently assessed; ATM supplies the context and discovery path for the outside party to inspect that assessment.

This example is fictional and offline. All hostnames use `.example`, no network request should be made, and no assessor has performed these tests. The illustrative report is Markdown, not a new standardized machine-readable report format. External report formats, authentication and trust policy remain implementation/profile responsibilities.

## 1. Read the publisher's claim and pointer

The [manifest fixture](../../examples/validation-chain/manifest.json) declares `interaction_profile.explicit_invocation_required: true`. Its `verification.verified_by` record names an assessor, claims a `pass`, lists that claim, and supplies `report_uri: https://assessor.example/reports/invocation-1`.

These fields are the **publisher's statements**. Neither naming another organization nor signing this manifest makes the embedded `pass` the assessor's authenticated statement. The report URI gives the visitor somewhere to look. Omitting the URI is permitted by the legacy schema but would not supply this discovery step.

## 2. Obtain the validator's statement

A visiting agent that permits this retrieval would follow the URI under its network and credential policy. In this offline illustration, use [the assessor finding fixture](../../examples/validation-chain/assessor-finding.md) in place of the network response.

Keep the two speakers separate. Compare the fetched finding with what the publisher said about it; a different result, missing claim or different subject is not repaired by the publisher's `pass` label. A report may itself contain further evidence links, which remain untrusted inputs until evaluated.

## 3. Establish provenance and applicability

The visitor needs an authenticated basis for attributing the finding to its actual author, rather than trusting an `entity` string or a copied logo. Depending on the report profile, this may involve a signature and independently selected issuer keys, or an authenticated publication channel. The profile must define that basis; the report cannot appoint its own trust anchor merely by naming one.

Then check the exact claim and value, assessed document/version, subject, deployment/scope, observation interval and relevant supersession/revocation status. This fixture includes the exact manifest-byte SHA-256 so the binding can be reproduced:

```bash
shasum -a 256 examples/validation-chain/manifest.json
```

The digest must match the finding's digest. That only shows which bytes the finding names. It does not authenticate the finding or prove the control works. The visiting agent must obtain its expected deployment independently, not adopt a report's scope simply because the report names it. A different deployment or claim cannot inherit this result.

## 4. Evaluate the finding's substance

Authenticated authorship is not synonymous with correctness. The visitor considers the method, observations, supporting records, limitations and assessor relationship under its own reliance policy. A domain-ownership check is evidence about domain control, not a test of a platform's invocation boundary. A shared domain can signal self-assessment; a different domain alone does not establish independence.

This fixture offers no authenticated assessor statement or actual observation records. Therefore its result remains unverified. In a real deployment with adequate authentic, applicable evidence, the visitor could accept the assessment for the covered claim; ATM does not prohibit that conclusion or require perpetual uncertainty. The decision is made by the relying party using the evidence, not by trusting the publisher's link alone.

## 5. State what was established

Report separately: the publisher's claim, whether the assessor's statement was authenticated, which claims/scope it covers, and the visitor's assessment of its evidence. Missing, inaccessible, stale, mismatched or unsupported evidence remains unresolved, not proof the publisher lied and not blanket trust.

Even an accepted control assessment is not permission to invoke an operation. The receiving platform retains its authorization and enforcement responsibilities.

## Current implementation boundary

The existing verification schema allows this discovery record but does not require the full external-report binding above or define a report wire format. Descriptive annotations make that boundary explicit without breaking existing documents. Repository tools validate structure and bounded local fixtures; they do not follow this link, authenticate the fictional assessor, or implement these reliance decisions. Tests check example consistency, not real third-party validation.

See [unreleased clarification notes](../../spec/validation-chain-clarification-notes.md) for compatibility and scope.
