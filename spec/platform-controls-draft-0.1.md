# Platform-control consumer profile 0.1 — unreleased proposal

This experimental profile tests [issue #1](https://github.com/filchyboy/agent-trust-manifest/issues/1) on the draft reference consumer. It is not ATM v0.3.0, a released extension, a resolution of the issue, or a runtime enforcement implementation. The v0.2.0 core and existing companion schemas and examples retain their contracts. An ATM 0.2.0 manifest can discover this sidecar through its existing `platform_policy` artifact type. Older consumers can inventory the reference without implementing this profile. Do not insert profile fields into the closed v0.2.0 core object.

Schema IDs ending in `platform-controls-draft-0.1.schema.json` and `platform-context-draft-0.1.schema.json` are local identifiers, not claims of hosted availability. The sidecar declares `profile_version: platform-controls-draft/0.1` and compatibility with ATM `0.2.0`. Future incompatible experimental changes must use a new profile identifier/schema; adopting mandatory core fields or changing core semantics requires a separately reviewed major contract version under the versioning policy. No tags or release metadata are changed here.

## Meaning and roles

ATM describes the receiving platform's controls and makes platform capabilities and their access/approval conditions discoverable. An agent's ability and its operator's consent cannot authorize a function the receiving platform does not permit. Listing, parsing, schema validation and declared evidence do not authorize a caller. The platform must independently enforce its current policy at invocation. Agent mandates and delegation protocols remain external.

The sidecar requires these separately named roles; one entity may occupy several roles without those roles becoming equivalent:

- `publisher.id`: publishing entity, bound by this demo to the manifest's `issuer.uri`. It need not equal the platform subject ID.
- `subject`: explicit `type: platform` and platform ID. Agent subjects are rejected even if IDs match.
- `scope`: exact deployment, tenant, surface and policy version. Use public, opaque fixture labels; do not publish customer identities or secrets.
- `control_authority.id`: party claimed to set platform policy for this scope.
- `enforcement_point.id`: claimed platform component applying that policy to actual invocations.
- `evidence[].assessor.id` and `relationship`: claimed assessor and self/independent/affiliated/unknown relationship. These labels disclose claims; they do not authenticate independence.

Roles do not carry signatures or endorsements. Structural validation does not authenticate any role, delegation or relationship. The historical `governance_artifacts[].owner` remains an artifact-maintenance responsibility label.

## Discovery and conditions

The positive fixture links a sidecar as one `platform_policy` artifact with its exact draft schema ID/version, a same-origin `/.well-known/platform-controls.json` URI, publication/expiry, digest, publisher, platform subject and surface scope. The consumer inventories this URL but never follows it. The exact bytes must be supplied explicitly using `--platform-profile-file`; digest matching binds them only to the supplied manifest. A self-reported `active` label remains unauthenticated and revocation is not checked.

Each capability declares `id`, `platform_permission` (`allowed`, `refused`, `unknown`), a nonempty list of `access_conditions`, and `approval_required`. `allowed` is a claimed platform condition for this scope, not a caller grant. Access-condition strings are displayed, never evaluated or fulfilled. `approval_required: true` is a prerequisite, never an approval receipt; `false` also grants no authority. There is no `approval_granted` input or agent-authorization field. The closed capability object rejects an injected approval receipt.

A listed capability is not a guarantee of caller eligibility. Missing, ambiguous or stale discovery leaves capability existence unresolved; it does not establish that a capability is absent. A declared refusal produces `hold`; the consumer neither invokes the capability nor enforces the refusal at runtime.

## Applicability and freshness

The consumer requires a separately selected expected-context file containing the platform subject, deployment, tenant, surface, capability ID and current expected policy version. It must not derive this expectation from the untrusted sidecar. Selecting an expectation is not an authorization grant or an assertion that the selected policy is actually current.

The profile must match the selected context exactly. This testbed supports no inheritance, aliases or wildcard matches. Wrong subject type is a structural rejection; wrong ID, tenant, surface, capability, deployment or policy produces an explained unresolved result. The reference publisher and subject are checked separately. The profile also binds to the manifest version and origin.

Exactly one assessment is supported. It covers the explicit `platform_capability_conditions` claim and repeats the full applicability binding. It also carries an `assessed_controls` snapshot of the control authority, enforcement point and complete selected capability declaration (ID, platform permission, access conditions and approval requirement). Exact comparison rejects an unchanged assessment after any of these roles or conditions changes, even if the policy version is reused and the publisher repins the sidecar. This is applicability checking, not authentication or proof of the snapshot. Its observation/expiry interval must include the decision time, with expiry strictly after observation and no future observation. A `pass` result is still only an unauthenticated declaration, not proof of safeguards or caller eligibility. Missing, ambiguous, stale, future-dated, failed or unknown assessment remains unresolved. Operational status cannot substitute for this assessment or prove invocation controls.

Reference, sidecar, manifest and assessment freshness are checked separately. Changed expected deployment/policy holds even if all documents remain unexpired. The consumer cannot detect an undisclosed policy change; the caller must independently select the current expectation. Maximum observation age, cache TTL, clock skew tolerance, trust anchors, issuer/assessor authentication, authoritative revocation and live enforcement remain unimplemented. Fixture time assumes an accurate clock and zero skew. These are issue #1 review decisions, not inferred production guarantees.

## Output and fixtures

Consumer report version `atm-consumer-demo/0.2` adds `platform_controls` and explicit unresolved caller eligibility, false approval/access grants and false runtime-enforcement status. It also rejects agent-typed legacy status subjects and unsupported subject qualifiers instead of ignoring them. The v0.1 report version was a draft consumer contract; old inputs remain structurally valid, but an unsupported subject can no longer pass the demo's applicability checks.

`platform_controls.declaration_checks_passed` refers only to the local declaration checks above. It does not mean the caller satisfies access conditions. A positive case remains `unverified` and at most `manual_review`; unresolved cases produce `hold`. Neither decision grants access. `approval_granted: false` means the consumer has issued or verified no approval, not that a live platform denied a particular approval request. Without the optional sidecar inputs, legacy checks remain available and `platform_controls` explicitly reports unresolved `profile_not_supplied`.

[Fixtures](../examples/consumer/platform-controls/) contain a positive manifest/profile/context and `cases.json`, an explicit mutation matrix applied to the positive profile. Tests repin mutated fixture bytes to show that schema-valid, digest-matched wrong-scope evidence still cannot match. The matrix covers subject-type and identifier mismatch; wrong tenant/surface/capability/deployment; changed policy; stale profile/assessment; future observation; refusal; unknown permission; missing capability/evidence; failed assessment; approval required/not required and receipt injection; wrong publisher/manifest version; and changes to assessed roles or capability conditions without a corresponding assessment snapshot. Additional tests cover tampering, missing discovery, ambiguous evidence/capabilities, paired CLI expectations, source-specific sidecar/context input errors that preserve inspected manifest/status results, and legacy subject-type rejection.

The positive case demonstrates discovery without caller authority. The platform-refusal and approval-required cases assume the acting agent has ability and operator consent as external facts; neither fact is consumed as authority. This is a bounded declaration test, not a claim to have tested runtime denial on a live platform.
