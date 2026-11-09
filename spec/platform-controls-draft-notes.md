# Unreleased platform-control profile changes

- Preserve all v0.2.0 schema bytes and existing example contracts; introduce separately versioned experimental sidecar/context schemas compatible with ATM 0.2.0.
- Discover explicit platform roles, scope/deployment/policy and capability prerequisites through the existing `platform_policy` artifact mechanism. Keep agent mandates external and caller eligibility unresolved.
- Add a positive fixture and explicit negative mutation fixtures for issue #1; check schema, digest, subject type, exact applicability and freshness independently.
- Advance the bounded consumer report to `atm-consumer-demo/0.2`, adding unresolved platform-control/caller states and rejecting agent-typed platform status evidence. Both decisions continue to grant no access or approval.
- Keep issue #1 open as the design decision record and draft PR #2 as an existing bounded testbed. These local changes do not edit either GitHub resource or publish any version.

Focused local review fixes: bind each assessment to the exact declared authority, enforcement point and capability-condition snapshot, and preserve inspected manifest/status states when requested sidecar/context input fails. Both remain declaration-only checks.
