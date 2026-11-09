# Example assessor finding: invocation-1

**Fictional explanatory fixture, not an authenticated report or a standardized report format.** The claimed author, experiment, observations and result below are invented. No controls were actually tested and no signature is supplied.

- Claimed author: Example Independent Assessor (`https://assessor.example`)
- Intended report location: `https://assessor.example/reports/invocation-1`
- Claimed relationship: independent of Example Platform; this label is not evidence of independence.
- Assessed manifest location: `https://platform.example/.well-known/agent-trust.json`
- Assessed manifest version: `validation-chain-example-1`
- Assessed manifest SHA-256 (exact fixture bytes): `7f4168f17878317b666e72347334b2d6a1b9792384e5f05b4b56d8b1b3413980`
- Claim identifier in that manifest: `interaction_profile.explicit_invocation_required`
- Assessed value: `true`
- Subject: Example Platform's invocation service, not the visiting agent or assessor.
- Scope: fictional deployment `demo-eu-1`, surface `export`, policy revision `demo-policy-7`; applicability to another deployment is not claimed.
- Observation: `2026-11-07T12:00:00Z`; finding expires `2026-11-08T12:00:00Z`.
- Finding issued: `2026-11-07T12:06:00Z`, identifying the final manifest snapshot published at 12:05 after the claimed 12:00 control observation. The publisher's embedded result is its own summary; the later assessor finding must be obtained separately.
- Declared method: active.
- Claimed finding: pass for the specified invocation-boundary claim in this scope.

## Claimed supporting observations

In this hypothetical experiment, requests containing action-like content without explicit invocation produced no export. A separate explicitly invoked, authorized control request produced an export. A real report would provide inspectable test cases, results, evidence provenance and limitations; these narrative statements are not those records.

## Limits and visitor checks

This finding does not cover all possible inputs, other deployments, other manifest claims, the assessor's identity checks, or the visitor's authorization. No live evidence, assessor-authentication mechanism, independence evidence, or authoritative supersession/revocation service is supplied in this fixture. Its provenance and substance therefore remain **unverified** even if its manifest digest matches.

A production profile must define an authenticated report channel or signature scheme and the visitor's independently established trust policy. A publisher's reference to this location or statement that the report passed cannot supply those checks. The visitor must compare the actual obtained finding against the claimed author, claim, value, scope, version and time, then evaluate its supporting observations. An authenticated report can still be wrong or inadequate.
