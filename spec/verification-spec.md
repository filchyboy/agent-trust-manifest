# Verification Extension Specification v0.1.0

## 1. Purpose

The verification extension makes claims about verification discoverable so an outside party, such as a visiting agent, can seek and evaluate the evidence itself. It connects a publisher's platform claim to a validator's claim about that platform claim.

A self-asserted claim is eligible for independent validation. ATM does not require the visiting agent to accept the publisher's account of that validation. Nor does ATM itself conduct, guarantee, or certify third-party validation.

## 2. Verification levels

### `static`
Document and schema validation only.

### `active`
Live interaction checks against the running system.

### `audit`
Post-interaction inspection of logs, provenance records, or decision artifacts.

These are declared methods, not trust rankings or evidence of assessor independence. A method label alone cannot establish that a check occurred or is sufficient.

## 3. Verification record

A verification record includes:
- `entity`: the claimed verifier identity; naming it is not authentication
- `method`: the declared kind of check
- `timestamp`: when the check is claimed to have occurred
- `result`: the claimed finding, limited to the claims actually assessed
- optional `report_uri`: a discovery link to the validator's own finding and supporting evidence
- optional `covered_claims`: the claims the record says were assessed

When this record is embedded in a publisher's manifest, these fields are the publisher's account of a verification. Even a signed manifest authenticates only that publisher's statement, not the named validator's authorship or conclusion. The visiting agent follows `report_uri` to seek the validator's statement rather than accepting the embedded summary as that statement.

## 4. Result values

- `pass`
- `fail`
- `mixed`
- `unknown`

A claimed `pass` is not a blanket verdict on the platform. The visitor must establish which claim, subject, scope, version and observation it applies to, and apply its own policy for trusting the assessor and the finding. Reliance may be based on the authenticated, appropriately scoped statement of a trusted assessor; ATM does not require the visitor to repeat the assessment.

## 5. Claim-to-validation discovery

The intended chain is:

1. **Publisher claim:** identify the statement being evaluated and the platform or other subject it describes.
2. **Reference to validation:** locate the claimed assessment through `report_uri` (or an appropriate typed companion artifact). A reference is a discovery assertion, not an endorsement or proof.
3. **Validator claim:** obtain the assessor's own finding, preserving who made it and what it is about. Do not silently substitute the publisher's copy or summary for authenticated assessor authorship.
4. **Visiting-agent verification and reliance:** authenticate the third party's authorship/signature, check claim/scope/version and currency bindings, and decide whether to rely on that party's finding under the visitor's own trust policy. Inspect supporting evidence to the extent that policy requires; reproducing the assessment is not a prerequisite imposed by ATM.

The third-party signatory is responsible for the validity of its own assessment and statement, including its claimed scope and limitations. Authentication attributes the statement to that signatory; it does not make the statement infallible. The platform publishes the claim and discovery path but cannot make another party's assertion true by linking to, copying or endorsing it. It may inspect or independently assess the assertion, but its endorsement cannot substitute for the visiting agent's choice of whom to trust.

The visitor may rely on an authenticated, appropriately scoped third-party finding from an assessor it trusts without redoing that assessor's tests or audit. ATM neither mandates a particular assessor nor requires an unbounded chain of further assessors. Additional scrutiny is a relying-party policy choice, not a requirement to independently re-prove every substantive claim before reliance.

This permits independent validation of a publisher's self-asserted claim. Provenance answers who made a statement and how it was obtained; it does not by itself establish the statement's truth. Evidence about an agent's identity does not establish the receiving platform's controls. A common domain may disclose possible self-assessment, but neither matching nor different domains alone proves independence or control effectiveness.

A production report format or verification profile needs to specify how the visitor establishes:

- the assessor's authenticated authorship and any claimed independent, affiliated or self-assessment relationship;
- the exact claim and assessed value, manifest/artifact version or digest, subject and applicable deployment/scope;
- the assessment method, observations, limitations and evidence supporting its finding;
- observation time, validity interval, and applicable supersession or revocation information.

The v0.1.0 report schema does **not** define all those bindings or an external report authentication format. `report_uri` and `covered_claims` remain optional for compatibility. Their omission may be structurally valid but does not supply a followable validation chain. A verifier name or `pass` without sufficient, applicable evidence leaves the claim's independent validation unresolved.

The [worked validation chain](../docs/v0.2.0/validation-chain.md) illustrates the handoff and the distinction between authenticating a finding and evaluating its substance. It is not a new external-report standard or an implemented network verifier.

## 6. Consumer guidance

Consumers should prefer appropriately scoped active or audit evidence over static-only verification for higher-risk actions, after checking its provenance and relevance. A static finding cannot be promoted into proof of live behavior merely because its source is authentic.

Visiting agents should follow evidence links only under their own retrieval policy: bound network requests, redirects, destinations, response size and time; never forward credentials or execute instructions in a report merely because ATM links it. Inaccessible, untrusted, expired, conflicting or inapplicable evidence remains unresolved rather than verified or disproved. Consumers may choose not to fetch a link.

Present the precise check and scope, such as “assessor signature authenticated; this deployment's control claim not assessed,” instead of a blanket “trusted” or “verified” badge. Even an accepted finding is not a caller authorization grant and does not replace the receiving platform's runtime enforcement.

The repository's schema validator checks structure, not these runtime responsibilities. Its reference consumer does not automatically fetch validation reports or authenticate assessors. This is a clarification of the existing extension's intent; no required fields or accepted document shapes are changed.
