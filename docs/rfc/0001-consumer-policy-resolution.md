# Issue #1: bounded decisions and remaining profile work

Status: proposed resolution record, 2026-11-09. [Issue #1](https://github.com/filchyboy/agent-trust-manifest/issues/1) remains open. This records implemented demonstration rules and recommended responsibility boundaries, not a production trust profile or a change to ATM wire schemas. It supplements [RFC 0001](0001-consumer-policy.md) and [RFC 0002](0002-third-party-claims-and-host-lifecycle.md).

## Decisions that follow from ATM's intent

- A publisher's assertion is eligible for independent assessment. A visitor authenticates the assessor's applicable finding and chooses reliance; it need not repeat a trusted assessor's work.
- Assessor identity, subject, publisher and control authority are separate roles. No URI equality, hash or declared independence label establishes their authority or the truth of their statements.
- Evidence sufficiency and trusted-provider selection belong to the relying party and the applicable claim-family profile, not a universal ATM assessor registry or compulsory reference validator.
- A current, applicable adverse finding is not the same as unavailable, expired, unknown or unauthenticated evidence. Host withdrawal and notification require the host's explicit policy and authenticated evidence; this consumer performs neither.
- Runtime platform permission is separate from discovery and reliance. Neither an agent's ability nor its operator's consent bypasses the receiving platform's current controls.

## Four-group decision and coverage matrix

All examples below are fictional, offline and unauthenticated. “Positive” means the local declaration checks pass, not that the claim is true or independently assessed.

| Group | Implemented demo rule | Positive coverage | Negative coverage | Remaining assumptions / profile decisions |
| --- | --- | --- | --- | --- |
| Origin, tenant and surface | Manifest origin and publisher match this demo's selected origin. Controls compare independently supplied subject, deployment, tenant, surface, capability and policy exactly; no inheritance. Publisher and subject remain distinct. | [Matching profile/context](../../examples/consumer/platform-controls/) exposes conditions, remains `manual_review`. | [Mutation matrix](../../examples/consumer/platform-controls/cases.json) covers wrong type/subject/tenant/surface/capability/deployment and changed policy; [tests](../../tests/test_platform_controls.py) cover duplicate matching companions and coexistence. | Production delegated hosting and portable tenant identifiers need an explicit authenticated binding profile. Use nonsecret identifiers; do not expose customer records or bearer credentials. Same-origin is a bounded demo choice, not a ban on independent assessors. |
| Minimum evidence and freshness | SHA-256 binds supplied raw bytes, not canonicalized JSON or authorship. Manifest, reference, profile and assessment are checked separately. Publication/observation must not be future-dated and decision time must precede expiry. Assessment snapshots must match selected conditions. | Matching current snapshot and digest. | Expiry boundary, future observation, tampering, changed controls even after rehashing, and old expected policy are covered by the matrix and [consumer tests](../../tests/test_consumer.py). | Accurate clock, zero skew and no independent maximum age are demo assumptions. Cache TTL is not enforced. Production profiles must define age/skew/cache and status freshness for their risk; no universal number is chosen here. Method labels alone do not establish sufficient evidence. |
| Failure handling | Missing, malformed, unsupported, stale, mismatched and nonpassing declarations hold with reasons. Valid declarations reach only manual review. No cache or retry fallback, no withdrawal, notification or caller denial action. | Matching declarations still grant no access or approval. | `test_declared_results_are_distinct_without_authentication_or_authority` and `test_stale_and_missing_findings_are_not_reported_as_failed_assessments` preserve failure distinctions; source-file and network tests cover unavailable/malformed input. | A hold is an unresolved local decision, not proof of falsity or capability absence. Host conflict, suspension, withdrawal, restoration and notifications remain RFC 0002 design work. |
| Issuer trust, independence and revocation | Every result stays unauthenticated. Declared issuer/assessor relationships and `active` status cannot promote authentication. Hashes only compare bytes. No outcome grants invocation authority. | A well-formed assessor declaration is displayed as unverified. | Existing rehashed-content and no-authority tests, plus `test_assessor_labels_and_claimed_active_status_do_not_authenticate`, reject trust promotion from self-description. | Trust anchors are selected independently by the visitor. A production profile must define authenticated authorship, key/channel binding, delegation and authoritative status discovery, including conflict/unavailability policy. No cryptosystem, provider registry or universal independence test is selected here. |

## Output refinement and compatibility

The demo adds `platform_controls.declared_assessment_result`, initially `null`. It contains the existing profile's `pass`, `fail` or `unknown` only after schema, binding, snapshot and freshness checks pass. It is explicitly a **declaration**, with `authentication: unverified`; it is not a verified substantive finding. A stale or mismatched claimed `fail` is not promoted into this field. Its specific unresolved reason remains available.

Existing `assessment_not_pass` and `hold` behavior is retained for compatibility. The added field distinguishes `fail` from `unknown` without changing those existing reason values. This closed platform-control profile has no `mixed` result; the generic verification extension does. No new schema result enum is added or implied.

The network worker's `incomplete_body` reason is now preserved through the sanitized wrapper. It means truncated transport, not a negative assessment. Unexpected worker stderr remains suppressed.

## What would permit broader resolution

The six platform-boundary acceptance criteria in issue #1 have offline declaration-level coverage: capability discovery, no operator-consent bypass, subject-type separation, exact scope, changed/stale policy handling, and approval-required not approval-granted. They do not demonstrate a live enforcement point or authenticate an assessor.

Before describing the broader trust questions as resolved, review a concrete claim-family/authentication profile and demonstrate:

1. Independently selected assessor/channel trust, exact claim revision and scope bindings, and a clear separation between authentication and reliance.
2. Freshness/status rules for that use case, including replay, supersession, revoked credentials and unavailable/conflicting status sources.
3. Independent producer/consumer interoperability, including rejection under one visitor's policy without labeling that visitor structurally nonconformant.
4. If host lifecycle is in scope, RFC 0002's authenticated adverse-finding, idempotent withdrawal/notification and restoration tests.

These are substantive profile choices, not defects to conceal with arbitrary defaults. Select a first real claim-family use case before choosing authentication conventions and numerical freshness policy. Host lifecycle can remain separately scoped. No issue closure, normative standard, live integration or independent assessment is claimed by this change.
