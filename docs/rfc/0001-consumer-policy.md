# RFC draft: scope, evidence and failure rules for an ATM consumer

Status: proposed questions for review; no public issue or standards outreach has been sent.

[Documentation index](../v0.2.0/index.md) · [Consumer contract](../v0.2.0/consumer.md) · [Worked example](../v0.2.0/worked-example.md)

## Context

The small reference consumer checks a fictional platform-scoped manifest and explicitly supplied status bytes. It inventories other evidence, detects stale or missing input and byte tampering relative to the supplied manifest, and returns `hold` or `manual_review`. It never grants access, authenticates a publisher, verifies a signature or tests live safeguards.

Operational status is not evidence that invocation boundaries or other substantive controls work. The following questions must be resolved before making broader trust or authorization decisions. These are review proposals, not additions to the normative schemas.

## 1. Origin, tenant and surface scope

- Should the profile require the fetched origin, manifest issuer URI/domain and artifact subject to agree? How should delegated hosting or an issuer operating multiple origins be represented without treating a URI match as proof of identity?
- What precisely identifies a tenant or surface, and how does a verifier bind an observation to that scope without publishing customer identities or bearer credentials?
- May evidence about a platform be used for a particular tenant or surface? If so, what explicit inheritance and exclusion rules prevent a broad report from being mistaken for a narrower assessment?

Proposed test boundary: a wrong origin, subject, audience or supported scope must not satisfy a relying party's requirement. Unsupported scopes remain unresolved rather than implicitly inherited.

## 2. Minimum evidence and freshness

- Which claims need active tests, audit evidence or signed declarations? What does a verification method cover, and what evidence is sufficient for a given relying-party action?
- How should publication/expiry, observation period, maximum age, cache TTL and clock skew interact? What invalidates an otherwise unexpired report after a deployment or policy change?
- Should a digest bind raw bytes or a specified canonical representation? Which report fields bind a result to the exact manifest/version/claims it examined?

Proposed test boundary: valid JSON or an operational-status assertion alone never satisfies a substantive safeguard requirement. Replay, stale observations and altered evidence fail the applicable profile even when schema-valid.

## 3. Failure handling

- Which failures require an explicit deny, a temporary hold or manual review? What distinguishes unavailable, missing, malformed, unsupported, expired and contradictory evidence?
- May unavailable services be retried or cached, and with what limits? Is stale evidence ever acceptable for a specifically bounded action?
- How should a consumer expose partial checks without making an unchecked claim look verified or implying that a successful parser grants access?

Proposed test boundary: no automatic access grant from missing, failed or unsupported checks. State and reasons remain visible; retry and retention policies are explicit and bounded.

## 4. Issuer trust, independence and revocation

- How does a relying party obtain trust anchors and authenticate the relationship between a publisher, verifier identity, signing key and assessed subject?
- How are verifier conflicts, self-assessments, delegated issuers and independence disclosed? What determines credibility for a named assessment method?
- Which authenticated source establishes key/report/issuer revocation, and what happens when it is unavailable, stale or disagrees with an artifact's own revocation label?

Proposed test boundary: a correct signature only authenticates a signing relationship defined by a profile; it does not prove a substantive claim. A self-reported `active` label is not an authoritative revocation check.

## Requested review format

For each group, propose a concrete rule, one positive fixture and at least one negative fixture, and identify remaining assumptions. Avoid requiring publication of private source code, customer records or operational secrets. Separate what is proposed, implemented, tested and independently assessed.

Suggested issue title: **Define consumer scope, freshness, failure and issuer-trust requirements**.

This document is ready to use as an issue body after review and explicit approval to post it. No delivery dates, certification or compatibility claims are introduced.
