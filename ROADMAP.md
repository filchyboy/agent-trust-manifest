# Agent Trust Manifest — Proposed Roadmap

## Purpose

ATM provides a vendor-neutral way for systems to declare their trust properties and for outside parties to evaluate the evidence supporting those declarations. Public specifications and verification methods remain separate from private platform implementations.

This roadmap proposes an implementation sequence and acceptance criteria. It does not promise delivery dates.

## Current release: v0.2.0 prerelease

The initial package contains specifications, JSON Schemas, fictional examples, and structural validation tooling. It establishes a common format for manifests and supporting artifacts.

The tooling does not yet verify signatures, test live behavior, conduct independent audits, or establish that a publisher’s claims are true.

## Roles

- Publisher: declares the system’s properties and publishes supporting artifacts
- Responsible component or role: maintains a particular artifact
- Verifier: evaluates specified claims using documented methods and reports evidence and limitations
- Relying party: decides whether the evidence satisfies its requirements

A party may perform more than one role, but those relationships must be disclosed. Self-declarations, signatures and independent verification must remain distinguishable.

## Milestone 1: A clear conformance baseline

Define the minimum requirements an implementer must satisfy, including required fields, extension behavior, compatibility, and treatment of missing or contradictory information.

Clarify specification, schema and release versioning. Document project decision-making, contributions, security reporting and open questions. Extend the threat model to cover false claims, compromised keys, replay, stale evidence, verifier conflicts and privacy leakage.

Acceptance: the minimum profile is documented and covered by positive and negative tests; an independent implementer can produce conforming artifacts without private guidance.

## Milestone 2: Signing and verification tooling

Define deterministic signing inputs, supported signature profiles, identity-to-key binding, key discovery, rotation, expiry and revocation.

Implement reference signing and verification tools with shared test vectors. Verification reports must identify the claims examined, relevant artifact versions, methods, results, timestamps and limitations. Define verifier discovery and how relying parties assess credibility and independence.

Acceptance: valid artifacts verify, while altered artifacts, wrong identities, revoked keys and expired evidence are rejected or explicitly classified as unverifiable. A valid signature must never be presented as proof that a substantive claim is true.

## Milestone 3: An independently verifiable pilot

Demonstrate a small set of concrete claims from publication through independent evaluation to a relying party’s decision.

The pilot should work through published artifacts and documented evidence interfaces without requiring access to the publisher’s private source repository. Claims beyond that evidence must remain clearly identified as assertions or outside the assessment’s scope.

Acceptance: a publisher and independent verifier complete the workflow; a second verifier implementation passes shared interoperability tests. Tests cover unavailable endpoints, malformed reports, stale evidence, replay and unsupported claims. Evidence access follows explicit disclosure and retention limits.

## Milestone 4: Deployment-bound attestation

Bind evidence to a specific deployment, configuration and observation period. Define which changes invalidate an assessment or require fresh verification.

Acceptance: consumers can distinguish evidence about the current deployment from evidence about an earlier or different system, and stale deployment claims fail predictably.

## Milestone 5: Reputation and federation

Define reputation events, evidence provenance, corrections, disputes and expiry. Develop federation rules and evaluate anti-Sybil controls, collusion and manipulation risks.

Acceptance: reputation inputs are traceable, correction mechanisms work, and independent implementations interoperate. Reputation remains evidence for a relying party’s decision, not an automatic grant of authority.

## Boundaries

ATM does not guarantee safety, regulatory compliance, insurance eligibility or certification. It should enable meaningful verification with minimal disclosure, without requiring publication of proprietary code, customer records or private operational details.

## Compatibility across milestones

Interoperability begins with conformance rather than being added at the end. Each integration will require a versioned profile naming the external specification, supported features, evidence boundaries and limitations.

### 1. Conformance

Map external identity and delegation concepts to ATM’s roles. Define minimal references preserving issuer, audience, resource, purpose and authorization scope where applicable. Document what each signal proves and what still requires independent evidence. Review licensing before adopting dependencies or distributing adapters.

### 2. Signing and verification

Bind scoped requests or authorization artifacts to the relevant manifest and verification report. Distinguish request signatures, manifest signatures and evidence of effective controls. Specify freshness, expiration, revocation, replay protection and unavailable-service behavior. Public artifacts must not contain credentials or payment data; references must not function as bearer credentials.

### 3. Independent pilot

Implement one narrowly scoped integration profile first. Publish reproducible interoperability tests covering altered artifacts, wrong identities or audiences, scope mismatches, replay, stale evidence, revoked keys and unavailable endpoints. Verification must not require private repository access. Unsupported or missing evidence must remain visibly unresolved.

### 4. Deployment attestation

Extend the tested bindings to deployment identity, configuration and observation period. Define how changes invalidate or limit prior evidence.

### 5. Reputation

Preserve each observation’s source, scope, freshness and verification method. Successful authentication or payment authorization must not automatically count as proof that other controls work.

### Acceptance rule

Claim compatibility only for named versions and tested capabilities, with reproducible results and disclosed limitations. Keep proposed, implemented, tested, certified and endorsed statuses distinct.
