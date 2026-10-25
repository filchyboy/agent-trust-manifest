# RFC draft: scope, evidence and failure rules for an ATM consumer

Status: open design decision record in [issue #1](https://github.com/filchyboy/agent-trust-manifest/issues/1). This local snapshot reflects the issue updated 2026-10-25. The experimental profile below is a bounded testbed proposal, not resolution of the issue or a change to the v0.2.0 core contract.

[Consumer contract](../v0.2.0/consumer.md) · [Draft platform-control profile](../../spec/platform-controls-draft-0.1.md)

## Context

The small reference consumer checks a fictional platform-scoped manifest and explicitly supplied status bytes. It inventories other evidence, detects stale or missing input and byte tampering relative to the supplied manifest, and returns `hold` or `manual_review`. It never grants access, authenticates a publisher, verifies a signature or tests live safeguards.

Operational status is not evidence that invocation boundaries or other substantive controls work. The following questions must be resolved before making broader trust or authorization decisions. These are review proposals, not additions to the normative schemas.

## Platform-control boundary

ATM describes the receiving platform's controls and makes its capabilities and access/approval conditions discoverable. An acting agent's ability and its operator's consent do not authorize a function the platform does not permit. Discovery and structural validation grant no authority: the platform must independently enforce its current policy at invocation. A listed capability does not guarantee that a particular caller is eligible. Missing or stale information is unresolved; it is neither permission nor proof that the capability does not exist.

Keep these roles and subjects explicit, even when one organization performs several roles:

- **Publisher:** the party publishing the manifest or evidence; publication alone does not establish control authority or assessment independence.
- **Platform subject / deployment / surface:** the receiving platform being described, including the exact deployment, tenant, exposed surface and capability to which a claim applies. An acting agent is a distinct subject type.
- **Control authority:** the party entitled to set the platform policy and required access or approval conditions for that scope.
- **Enforcement point:** the platform component that applies current policy to the actual caller and invocation, including any required approval.
- **Assessor:** the party evaluating a specified claim about a specified subject, method and observation period; it may be independent or self-assessing, which must be disclosed.

Evidence about an agent must not satisfy a platform-control claim merely because identifiers match. ATM does not become an agent mandate or delegation protocol, and an agent/operator authorization is not a substitute for the receiving platform's permission.

## 1. Origin, tenant and surface scope

- Should the profile require the fetched origin, manifest issuer URI/domain and artifact subject to agree? How should delegated hosting or an issuer operating multiple origins be represented without treating a URI match as proof of identity?
- What precisely identifies a tenant or surface, and how does a verifier bind an observation to that scope without publishing customer identities or bearer credentials?
- May evidence about a platform be used for a particular tenant or surface? If so, what explicit inheritance and exclusion rules prevent a broad report from being mistaken for a narrower assessment?
- How are subject type, deployment, tenant, surface and capability bound explicitly to each platform-control claim? Reject subject-type mismatch, and do not silently match evidence from another deployment, tenant, surface or capability, even when other identifiers agree.

Proposed test boundary: a wrong origin, subject, audience or supported scope must not satisfy a relying party's requirement. Unsupported scopes remain unresolved rather than implicitly inherited.

## 2. Minimum evidence and freshness

- Which claims need active tests, audit evidence or signed declarations? What does a verification method cover, and what evidence is sufficient for a given relying-party action?
- How should publication/expiry, observation period, maximum age, cache TTL and clock skew interact? What invalidates an otherwise unexpired report after a deployment or policy change?
- Should a digest bind raw bytes or a specified canonical representation? Which report fields bind a result to the exact manifest/version/claims it examined?
- How are the applicable control authority, policy version and approval conditions bound to the assessed deployment and capability? A deployment or policy change must trigger an explained `hold`/unresolved result until applicable evidence and conditions can be established; a still-valid schema or unexpired report is insufficient.

Proposed test boundary: valid JSON or an operational-status assertion alone never satisfies a substantive safeguard requirement. Replay, stale observations and altered evidence fail the applicable profile even when schema-valid.

## 3. Failure handling

- Which failures require an explicit deny, a temporary hold or manual review? What distinguishes unavailable, missing, malformed, unsupported, expired and contradictory evidence?
- May unavailable services be retried or cached, and with what limits? Is stale evidence ever acceptable for a specifically bounded action?
- How should a consumer expose partial checks without making an unchecked claim look verified or implying that a successful parser grants access?
- How are platform refusal, unresolved eligibility and additional approval communicated upfront? `approval_required` must never imply `approval_granted`; an operator-authorized agent must not bypass a platform refusal or required additional approval. Missing or stale discovery/evidence must remain unresolved without asserting that the capability does not exist.

Proposed test boundary: no automatic access grant from missing, failed or unsupported checks. State and reasons remain visible; retry and retention policies are explicit and bounded.

## 4. Issuer trust, independence and revocation

- How does a relying party obtain trust anchors and authenticate the relationship between a publisher, verifier identity, signing key and assessed subject?
- How are publisher, platform subject/deployment/surface, control authority, enforcement point and assessor distinguished and their relationships authenticated? Neither a shared identifier nor a valid signature establishes that agent evidence supports a platform-control claim or that a publisher/assessor may authorize an invocation.
- How are verifier conflicts, self-assessments, delegated issuers and independence disclosed? What determines credibility for a named assessment method?
- Which authenticated source establishes key/report/issuer revocation, and what happens when it is unavailable, stale or disagrees with an artifact's own revocation label?

Proposed test boundary: a correct signature only authenticates a signing relationship defined by a profile; it does not prove a substantive claim. A self-reported `active` label is not an authoritative revocation check.

## Acceptance criteria

The design decision must define rules and positive/negative fixtures demonstrating that:

- A platform capability and its access/approval conditions can be discovered without granting the caller authority or guaranteeing caller eligibility.
- An agent with the ability and operator consent to perform a function cannot bypass the receiving platform's refusal or required additional approval. Current policy remains independently enforced by the platform.
- A subject-type mismatch is rejected: evidence about an agent cannot satisfy a platform-control claim, including when identifiers match.
- Evidence for the wrong tenant, surface, capability or deployment cannot silently satisfy the claim. Any permitted inheritance must be explicit and bounded.
- Stale evidence or changed deployment/policy produces an explained `hold`/unresolved result. Missing or stale information grants no permission and does not establish that the capability is absent.
- `approval_required` does not imply `approval_granted`; discovering or structurally validating an approval condition does not fulfill it.

## Requested review format

For each group, propose a concrete rule, one positive fixture and at least one negative fixture, and identify remaining assumptions. Avoid requiring publication of private source code, customer records or operational secrets. Separate what is proposed, implemented, tested and independently assessed.

## Reference implementation

Draft pull request: https://github.com/filchyboy/agent-trust-manifest/pull/2

Keep this issue as the open design decision record. Draft PR #2 is a bounded consumer testbed for the proposed rules and fixtures; it does not resolve these design questions or implement runtime enforcement. Runtime enforcement of current platform policy remains the platform's responsibility.
