# Design proposal: third-party findings, rating normalization and host claim lifecycle

Status: unreleased design proposal, 2026-11-08. This document fleshes out the claim-to-validation model without changing the ATM v0.2.0 wire contracts or implementing a host workflow. It complements [RFC 0001](0001-consumer-policy.md), the [verification extension](../../spec/verification-spec.md), and the [reputation extension](../../spec/reputation-spec.md). It does not close issue #1 or supersede the narrower experimental platform-control profile.

## 1. Intended outcome

A tenant publishes a claim through a hosting platform. The platform makes the claim and links to relevant third-party findings discoverable through ATM. A visiting agent can follow those links, authenticate who made each finding, determine exactly what it concerns, and decide whether to rely on that third party. The signatory is responsible for its own statement; ATM and the host do not certify its truth by carrying it.

The ecosystem can include technical assessors, industry certification bodies, business-rating services, auditors and other parties whose judgments visitors find useful. ATM does not designate universally trusted providers. A visitor may trust a reputable third party's authenticated, applicable statement without repeating its audit. Another visitor may decline to trust that party or require additional evidence. No infinite chain of assessors is required.

This model separates the party making a claim, the subject of the claim, the party publishing it, and the party assessing it. A tenant may be a claimant and subject without being the platform operator. A provider's statement about a business must not silently become a statement about the hosting platform's technical controls.

## 2. Responsibility boundaries

| Actor or layer | Responsibility | Does not establish |
| --- | --- | --- |
| Tenant/claimant | Supplies its own assertion and relevant scope; corrects it when appropriate | Independent truth merely by asserting it |
| Host/publisher | Publishes accurate references; manages its own claim-admission, display, withdrawal and tenant-notification policy | The third party's authorship or substantive correctness by copying or endorsing it |
| Third-party assessor/signatory | Owns the assessment, methodology, scope, limitations and findings it issues; signs when its profile uses signatures | Universal trust or authority over unrelated claims |
| Normalizing publisher/adapter, if separate | Owns the transformation from provider-native data to an ATM-compatible representation and identifies that transformation | That the original assessor signed the transformed bytes |
| Visiting agent/relying party | Authenticates statements and bindings, selects trusted sources and decides reliance under its own policy | Platform access permission from a favorable rating alone |
| ATM protocol/profile | Defines interoperable representations, discovery and meaning | Provider reputation, truth, host workflow execution or notification delivery |
| Optional reference tools | Perform their documented parsing and demonstration checks | A mandatory implementation or a certification service |

The host may inspect or independently assess a third-party finding. What it cannot do is make that finding true by linking to it, or replace a visitor's trust decision with its own endorsement. Host publication acceptance and visitor reliance are separate decisions even when they use the same evidence.

## 3. Claim and finding bindings

An interoperable profile for a particular claim family should define the following concepts. These are design requirements for that profile, **not new fields accepted in the current closed core schema**:

- Stable claim identity plus exact revision, digest or other unambiguous version binding.
- Claimant, publisher and subject, with each role named separately.
- Claim predicate and value, with a vocabulary/profile defining their meaning.
- Applicable tenant, deployment, surface, capability or business scope, without leaking private tenant identifiers.
- Assessor identity and the authenticated basis for attributing its statement, including key-to-identity binding where signatures are used.
- Assessment method, finding, observation period, validity interval and disclosed limitations.
- Evidence location, integrity binding, and an authoritative method of discovering supersession or revocation when the profile requires it.
- Any normalization or intermediary transformation, including its responsible party and version.

The visitor compares those bindings against the claim it is actually considering, not against an expectation invented by the untrusted report. A platform-level report does not automatically cover every tenant; one tenant's result does not cover another; a report for a prior claim revision cannot silently cover a changed assertion. Profiles must define any permitted inheritance explicitly.

Current ATM offers `verification.verified_by[].report_uri` and `verification.verified_by[].covered_claims`, and companion artifacts with issuer, subject, scope, version and hash. These are useful discovery building blocks, not a complete authenticated claim/finding protocol. The legacy verification fields remain optional and do not enforce those bindings. The platform-control draft models only a specific platform-capability claim, not every tenant assertion. Do not insert arbitrary new top-level fields into the closed core schema or advertise the proposed profile as implemented.

## 4. Provider-native ratings and bounded normalization

A BBB-style native grade such as `A+` need not become a new ATM enum value. A signatory can publish an ATM-compatible representation using the existing enum, while preserving the original grade and the mapping's provenance in its published methodology and linked evidence. ATM's schema and local validator should not be responsible for every raw string, type or format produced by every source.

For example, a fictional provider can explicitly map its native `A+` to ATM `excellent`. That is this provider's disclosed mapping, not a claim that all `A+` ratings mean `excellent` or that every provider uses comparable scales. The provider should explain the source scale, mapping version, loss of detail, treatment of unmapped values and whether an overall grade can meaningfully support a particular dimension.

The existing schema is intentionally bounded:

- `rating` uses `excellent`, `good`, `fair`, `poor`, or `unknown`.
- `result` uses `pass`, `fail`, `mixed`, or `unknown`.
- Numeric `score` is optional and its scale belongs in the methodology.
- `methodology.rating_scale` documents interpretation; it does not override the `rating` enum.
- Declared dimensions use the schema's vocabulary. Do not mislabel a broad business grade as `execution_safety`, for example. An overall-only representation is structurally possible with an empty `dimensions` array; a consumer profile may require more for its use case.

Unrecognized native data should not be coerced into a favorable rating. A mapping can produce `unknown`, omit a specific optional rating, or decline to produce a compatible finding, according to its documented policy. Preserve the raw source in the provider's format at a referenced location with appropriate integrity and provenance evidence. The visitor may retrieve it, but the generic ATM validator need not parse or validate that raw format. A future claim-family profile is warranted only when a concrete interoperability need cannot be represented faithfully, not merely because another provider uses a different spelling.

### Who signed the mapped finding?

If the original provider authors and authenticates the normalized feed, it takes responsibility for that representation and its mapping. If a host or independent adapter performs the mapping, the adapter must identify itself as the transformed feed's issuer and preserve the original provider's statement separately. An original signature cannot be copied onto changed bytes. Verifying a source signature does not authenticate the adapter's transformation; the visitor decides whether to trust each relevant party.

The [fictional mapped-rating example](../../examples/rating-normalization/README.md) demonstrates the existing wire fields, a linked provider-native source and a versioned methodology. It is not a BBB integration, an assertion about BBB methodology, or a cryptographically authenticated example.

## 5. Host publication lifecycle

The following is a proposed **host policy**, distinct from the portable protocol. A hosting implementation that adopts it should remove an affected claim from its current advertised/accepted claim set when a fresh, authenticated and applicable adverse finding meets its configured decision policy, and notify the affected tenant. This does not erase the original assertion or the assessment history. It also does not permit the host to revoke a third party's own signature or report.

Keep these states separate rather than reducing them to a single `valid` boolean:

1. Source availability: retrieved, unavailable, malformed, unsupported.
2. Authentication: established, invalid, unresolved.
3. Applicability: matches, mismatched, stale, superseded, unresolved.
4. Substantive assessment: pass, fail, mixed, unknown, or a mapped rating.
5. Host publication decision: active, suspended, withdrawn, awaiting review.
6. Tenant notification delivery: pending, delivered, failed, acknowledged where supported.

These are design concepts, not new ATM enum values. The exact internal state vocabulary is the host's choice. A portable profile should expose the relevant public state, reason, effective time and evidence reference without publishing private workflow or tenant-contact data.

| Observation | Meaning | Proposed host treatment |
| --- | --- | --- |
| Fresh, authentic, scope-matched adverse finding from a policy-accepted assessor | Substantive evidence against the covered claim | Withdraw the affected advertised claim and notify the tenant; retain the finding and decision history |
| Conflicting applicable findings | Assessors disagree | Apply the host's disclosed conflict policy; suspend or route to review if unresolved, without hiding the conflict or arbitrarily choosing the latest arrival |
| `mixed` or an adverse mapped grade | Partial or graded result | Evaluate covered subclaims and configured thresholds; do not equate every non-`pass` with falsity |
| Provider unavailable, timeout or temporary network error | Cannot currently obtain evidence | Retry/cache within bounded policy; if evidence becomes insufficient, suspend assurance or publication as policy requires, not mark the claim false |
| Finding expires | Evidence no longer current enough for this decision | Seek renewal or reassessment; suspend reliance/publication if required and tell the tenant the reason is expiry |
| Signature invalid or issuer/key trust unresolved | Cannot rely on the attributed statement | Reject that evidence and flag the authentication problem; this alone does not establish that the underlying claim is false |
| Wrong tenant, claim revision, deployment or scope | Finding does not apply here | Reject it for this claim; no cross-tenant withdrawal based on mismatched evidence |
| Assessor retracts or supersedes its finding | Prior finding's status changed | Re-evaluate affected publication decisions using authenticated status and replacement evidence; distinguish retraction from a substantive failed reassessment |
| Tenant edits the claim | Prior evidence may no longer cover it | Rebind/reassess; never silently inherit the previous revision's favorable result |
| New satisfactory finding after withdrawal | Possible grounds for restoration | Verify all bindings and policy prerequisites, then publish a new revision/state and notify the tenant; preserve the earlier adverse history |

No arbitrary negative report should trigger withdrawal. The host must establish assessor authority/trust for its own publication policy, authentication, exact claim applicability, temporal ordering and conflict handling before acting. The host does not have to reproduce the assessor's work, but it must not treat a mere URL or unauthenticated `fail` as an accepted adverse finding.

## 6. Withdrawal, versioning and cache safety

Withdrawal means removing the claim from the host's **currently advertised accepted claims**, not pretending the claim or failed finding never existed. Keep an audit record of the assertion revision, relevant assessment, decision policy/version, reason and time. Retention and privacy rules govern storage and access.

Publish a new manifest or companion revision and update discovery references/digests atomically enough that a reader cannot mistake an old favorable claim for the new state. A protocol profile needs stable claim IDs, effective status times, supersession/revocation semantics and cache behavior. A host can publish its own withdrawal decision, but that decision's issuer must remain the host, not the assessor.

The existing revocation feed can describe `trust_claim` entries with `revoked`, `expired`, `superseded` and reasons. It does not yet define a complete claim-lifecycle profile, authoritative withdrawal semantics, conflict ordering or an `assessment_failed` reason. Do not force a new meaning into an existing reason code without a reviewed profile/version change. Visitors with cached data must be able to discover relevant status changes according to the profile's freshness policy; a silent deletion alone is insufficient for that guarantee.

## 7. Tenant notification and remediation

Notification is a host responsibility, not an instruction an arbitrary evidence document can execute. Contact destinations come from the host's authenticated tenant configuration, not from a provider-controlled link or message body.

A proposed notification includes the affected claim/revision, what changed, the assessor and source finding when shareable, the host's publication action, effective time, and the distinction between an adverse finding and missing/expired evidence. It supplies a review/remediation path without asserting more than the evidence supports.

The host should record a durable notification event alongside the publication decision, use an idempotent event key, retry transient delivery failures with bounds, and expose persistent delivery failure to an operator. Delivery failure must not roll back a protective withdrawal; recording an event must not be labeled successful delivery. Duplicate/replayed findings must not cause repeated tenant messages or repeated state transitions. Reinstatement needs its own verified decision and notification rather than an automatic undo on the next successful HTTP request.

Appeals, correction requests, contradictory assessments, reassessment timing and human review are policy decisions that should be explicit. No external communications or host actions are performed by this repository's examples.

## 8. What belongs in a portable profile versus the host

**Portable:** claim and assessment identifiers; issuer/subject separation; claim/version/scope bindings; authentication and key-discovery conventions; normalized rating semantics and mapping provenance; finding/status/expiry/supersession meanings; public evidence references; freshness and retrieval expectations sufficient for independent implementations.

**Host-specific:** trusted-assessor selection for admission, thresholds, handling conflicts, publication-removal policy, tenant-contact channels, retry/outbox implementation, audit storage, private remediation workflows and enforcement at invocation.

**Visitor-specific:** trusted signatories, acceptable profiles and mappings, evidence age/risk thresholds, retrieval limits and final reliance decisions. Host acceptance is a discoverable fact about the host's policy, not a requirement that the visitor accept the same provider.

The platform-control demo's `hold`/`manual_review` outputs do not implement this lifecycle. Its `assessment_not_pass` result intentionally groups nonpassing declarations for a bounded demonstration, so it must not be reused as a production instruction to withdraw or notify a tenant.

## 9. Implementation and interoperability acceptance plan

Before claiming this design is implemented, test at least:

- Two independent assessors and two independently implemented visitors; optional reference tools are not required.
- Validly signed, scoped findings accepted under one visitor's policy but declined under another's, without either being called structurally nonconformant for its trust choice.
- Provider-authored normalized feed and adapter-authored normalized feed, preserving both speakers and rejecting copied signatures over transformed bytes.
- A native `A+` mapping to an allowed enum with retained source/methodology; unknown native value does not become favorable; a raw provider document is not incorrectly validated as an ATM feed.
- Wrong tenant/subject/revision/deployment, altered bytes, stale findings, revoked keys, invalid signatures and replayed older statuses.
- Authentic applicable failure causing exactly one withdrawal and one durable notification event; duplicate processing and concurrent refresh cannot restore the stale claim.
- Provider outage and expiry producing their own states and reasons, not false substantive failures; recovery alone does not override a still-current adverse assessment.
- Conflicting findings, partial/mixed results and policy changes; recorded rationale rather than silent flattening.
- Notification transient/permanent failure, retries, deduplication and delivery/acknowledgment distinction.
- Restoration after a new accepted finding, including a new publication revision and retained audit history.

Today's changes provide documentation, a schema-compatible normalization example and offline consistency checks only. They do not implement signature verification, assessor onboarding, a tenant claims UI, provider polling, withdrawal, notifications or conflict resolution. No schema expansion is required to illustrate the rating normalization. Any subsequent normative claim-lifecycle profile needs its own reviewed contract, fixtures and compatibility decision.
