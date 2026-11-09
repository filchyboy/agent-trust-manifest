# Proposal: a business-rating evidence profile

Status: design candidate, 2026-11-09. **Not an implemented protocol or a conformance claim.** This proposal narrows [RFC 0002](0002-third-party-claims-and-host-lifecycle.md) to one fictional BBB-style business-rating use case. It changes no ATM schema, enum, validator requirement or released contract. BBB is an illustration of a kind of assessor, not a participant, integration or endorsement.

## Purpose and actors

A fictional tenant, Example Bicycle Repair, claims it currently has a rating from Example Business Assessor. Its hosting platform publishes ATM discovery references. The assessor publishes its own assessment. A visitor authenticates that statement, checks which business and claim it covers, and decides whether that assessor and methodology satisfy its policy.

The assessor owns the substantive finding. The host owns its publication/admission decisions. The visitor owns its reliance decision. ATM connects those statements; neither ATM nor the host makes an assessor's conclusion true. A visitor may rely on a trusted assessor without repeating the assessment. No reference tool, universal trust registry, universal signature format or global assessor list is required.

## Proposed binding record

The following are requirements to settle in a separately versioned external evidence profile, **not fields to insert into the closed ATM core or reputation-feed objects**. An independently implemented visitor needs all of these bindings before relying on this use case:

| Concept | Proposed rule |
| --- | --- |
| Profile | Identify an exact profile revision and authentication variant. Unknown revisions remain unsupported, not silently downgraded. |
| Claim | Identify a stable claim ID, revision, predicate, exact asserted value and digest of the immutable claim representation. A human-readable sentence alone is insufficient. |
| Parties | Identify claimant, hosting publisher, business subject, assessor and any adapter separately. Use public opaque identifiers; do not publish private tenant records. |
| Scope | Bind the business subject to the exact tenant claim under consideration. A business rating says nothing about the host's execution controls or another tenant. |
| Finding | Identify an immutable assessment ID/revision, assessor-native grade, normalized value, observation time, validity interval and limitations. A rating is not automatically a `pass` on unrelated predicates. |
| Methodology | Bind the exact methodology and normalization version, source URI and digest; preserve source grade, scale and any lost distinctions. |
| Content integrity | For this candidate, digests mean SHA-256 over the exact retrieved representation bytes, with a lowercase 64-hex digest. Whitespace changes create different bytes. A digest never authenticates the issuer. |
| Current status | Identify the assessor's authoritative status source and assessment ID. Bind status revision, effective time, publication/expiry and any replacement assessment. A publisher's copied `active` is not authoritative. |

The visitor compares these against independently selected expectations for the claim and subject. It does not let an untrusted report choose its own expected subject or trusted assessor. Binding a finding to a claim prevents substitution; it does not prevent the assessor from being mistaken.

The wire representation, media type and discovery relation for this record remain open design decisions. A Markdown illustration or arbitrary new object in `issuer` is not an interoperable encoding. The current `report_uri` and `governance_artifacts` links can discover external evidence, but do not themselves implement this binding record.

## Normalized rating

Use the existing [fictional normalization example](../../examples/rating-normalization/README.md): a provider-native `A+` can be represented by `overall.rating: excellent` under a documented provider-specific mapping. This is not a universal equivalence. An overall business grade must not be relabeled `execution_safety`; `dimensions` can remain empty for this illustrative overall-only use case. Unknown native values must remain unresolved or map to `unknown`, not become favorable by default.

Prefer assessor-authored normalized output for the first pilot: it avoids a second speaker and transformation trust decision. If an adapter produces it instead, authenticate the adapter's output separately, retain the original assessor statement, and disclose both identities. A signature on source bytes cannot be transferred to different normalized bytes. The generic ATM validator need not understand the assessor's raw proprietary format.

## Two authentication variants to evaluate

### A. Authenticated assessor publication

The visitor obtains the finding and status directly from an HTTPS origin that its own policy already binds to the assessor, or from a delegation authenticated under that policy. A URL supplied only by the tenant does not establish that binding. Certificate validation, exact origin checks and bounded redirect/retrieval rules are necessary; arbitrary cross-origin redirects cannot inherit assessor identity. Domain control proves control of that publication channel, not organizational reputation or rating accuracy.

A digest pins the retrieved bytes, while the authenticated channel attributes their publication. An offline copy loses that channel evidence unless an independently verifiable receipt or signature preserves it. This variant is appropriate to evaluate for live retrieval, not a claim of portable offline authenticity.

### B. Signed portable evidence

Use an established envelope such as detached JWS or DSSE rather than inventing an ATM signature encoding. A selected profile must define exact payload bytes and media type, protected metadata, algorithm allowlist, signature encoding, trusted key discovery/binding, rotation and compromise behavior. It must reject `none`, empty or invalid signatures and unknown algorithms. Key URLs contained in untrusted evidence must not become trust anchors merely because they resolve.

For a raw-byte detached envelope, sign the immutable evidence payload, not a JSON object containing its own signature. If a future variant chooses canonical JSON, it must name the canonicalization algorithm and ship test vectors; consumers must not guess between raw bytes and canonicalization. A valid signature attributes a statement under the established key binding; it does not prove the rating is true.

**Decision still required:** select and specify one authentication variant for the first interoperability pilot. Neither is mandated for all ATM users. The legacy reputation schema requires a `signature` object but defines no interoperable signing procedure: do not fill it with `none` or placeholders and claim authenticated profile conformance. The relationship between an external authenticated record and that legacy field needs an explicit versioned decision before implementation.

## Freshness, status and replay

The candidate requires `observed_at <= published_at < expires_at`; reliance requires an observation not in the future and decision time before expiry. A production profile must additionally choose maximum assessment age, clock-skew tolerance, status age, cache bounds and outage behavior for its risk. These values are deliberately not invented here. A pilot is not complete until they are explicit and testable.

Retrieve authoritative status under the same established assessor authority, or a separately authenticated delegation. Compare status for the exact assessment ID, retain a monotonic revision/effective-time watermark, and reject rollback below a previously accepted revision. A first-time visitor still needs a fresh authoritative response; a local watermark alone cannot prevent first-contact replay. Signed payloads without a current-status mechanism cannot guarantee that an assessment or key has not been withdrawn.

Distinguish assessment withdrawal, supersession, expiry and signing-key compromise. The profile must specify whether historical signatures remain usable after key retirement and how compromise invalidates affected intervals. Do not translate an unreachable status service into a negative rating. If current evidence is insufficient, reliance is unresolved under the visitor's outage policy. An older favorable finding must not override a known later adverse finding simply because its expiry is later.

## Host handling and visitor outputs

Maintain separate authentication, applicability, currency, substantive finding and policy-decision states. An authentic applicable adverse rating can trigger host withdrawal of the affected advertised claim under its disclosed policy, followed by a durable tenant notification. A timeout, expired record or invalid signature is an evidence problem, not proof that the business lied. Preserve assertion/finding/decision history; restoration requires a new verified decision, not merely restored connectivity. See [RFC 0002's lifecycle](0002-third-party-claims-and-host-lifecycle.md#5-host-publication-lifecycle).

A host cannot retract the assessor's statement, and host acceptance does not force visitor acceptance. No rating, schema-valid document or favorable finding grants platform access.

## Gate before implementation or interoperability claims

1. Specify the external wire record, claim representation and exact profile identifier; settle how it links to existing ATM discovery and legacy signature fields without silently changing them.
2. Select one authentication variant and publish exact retrieval/key/discovery rules plus positive and negative test vectors. Document the alternative rather than claiming both work.
3. Set numeric freshness/status/cache/skew parameters for this pilot and specify authoritative status and replay behavior.
4. Exercise two independent visitors against assessor-authored normalized evidence: trusted by one visitor, declined by another without treating the trust difference as structural nonconformance.
5. Test altered bytes, wrong subject/claim revision, changed mapping, unknown grades, stale/withdrawn findings, status rollback, first-contact replay, compromised keys, copied adapter signatures and unavailable sources.
6. Verify host withdrawal/notification separately if a host implementation is built. Reference consumers and validators remain optional.

This proposal provides a concrete next design target, not a signing implementation, a live BBB feed, production evidence retrieval, or a reason to close issue #1.

## Subsequent optional provenance pilot

The [detached signing profile v1](../../spec/signing-profile-v1.md) selects a
concrete portable JWS variant for a separate platform invocation-claim pilot.
It does not implement this business-rating proposal, replace its provider-native
normalization, or mandate signing over the authenticated assessor-origin
publication variant A. Existing `assessed_controls` snapshots remain valid
within their own draft semantics. See the [fictional demonstration](../../examples/signing/README.md).
