# Reference consumer: a bounded demonstration

[Documentation index](index.md) · [Worked example](worked-example.md) · [Design review](../rfc/0001-consumer-policy.md)

The consumer displays four declared interaction controls, inventories evidence, and evaluates one explicitly supplied operational-status file. It is a demonstration profile, not a general trust engine, a conformance certification tool, or a live verifier of the declared safeguards.

## Inputs and commands

Use the Python environment from the [README](../../README.md#quick-start). The existing `jsonschema` dependency provides structural checks; optional detached authentication also uses the pinned `cryptography` dependency.

Offline:

```bash
.venv/bin/python tools/consumer/consume.py \
  --manifest examples/consumer/manifest.json \
  --expected-origin https://consumer-demo.example \
  --status-file examples/consumer/operational-status.json \
  --at 2026-10-06T18:00:00Z
```

The expected origin is chosen by the operator, not derived as an authority from the manifest. `--at` is for repeatable offline fixtures only. Without it, the decision uses the current UTC clock.

Network mode:

```bash
.venv/bin/python tools/consumer/consume.py --origin https://your-public-host.example
```

The host above is fictional; replace it with an operator-selected public HTTPS origin. This fetches only `/.well-known/agent-trust.json`. Evidence URLs are never followed. To check status bytes, independently obtain them through an appropriate trusted workflow and pass their explicit local path with `--status-file`. The consumer does not authenticate how that file was obtained. `--at` and `--expected-origin` are rejected in network mode.

The CLI writes a JSON report. Exit 0 means the result is `manual_review`, not that access is allowed or trust is established. Exit 1 means `hold`; argument-parser usage errors use exit 2.

## What is checked

- UTF-8 JSON, duplicate-key rejection, finite numbers and bounded structure.
- Existing local manifest and operational-status schemas, without remote schema retrieval.
- ATM core version `0.2.0` for this demonstration profile.
- Manifest publication/expiry timestamps and issuer URI/domain hints against the expected origin. A claimed match is not authenticated organizational identity.
- Exactly one operational-status reference with version `0.2.0`, the existing schema identifier, the exact same-origin `/.well-known/operational-status.json` URI, and platform scope. Tenant and surface scopes are not supported by this profile.
- Required publication/expiry metadata on the selected reference, a claimed `active` revocation label, and a lowercase `sha256:` digest of the exact supplied status bytes.
- Status feed version `0.2.0`, publication/expiry, claimed issuer/subject/scope alignment, and its declared operational state.

Hashing uses the raw file bytes, including whitespace and the final newline. It does not implement JSON canonicalization or signing. A digest match detects changes relative to the supplied manifest. An attacker who changes both the manifest and the status bytes can produce a new matching digest.

## State and decision contract

| Report field/state | Meaning |
|---|---|
| `manifest.state: fresh` | Inspected publication/expiry timestamps contain the decision time. |
| `missing` | Required input, selected reference or freshness metadata is absent. |
| `invalid` | Parsing, supported schema/profile, digest or scope checks failed. |
| `stale` | The inspected expiry is at or before the decision time. |
| `status_evidence.state: unverified` | Even a supplied, structurally valid, fresh, digest-matched file is not independently authenticated or audited. |
| `available_evidence[].state: unverified` | A reference or embedded extension is present; its truth/authenticity was not verified. |
| `policy.decision: hold` | One or more demonstration prerequisites failed. |
| `policy.decision: manual_review` | Original triage prerequisites passed; optional authentication and per-claim acceptance are reported separately, with remaining evidence limits still visible. |
| `policy.access_granted: false` | Neither decision grants access or approves an action. |

Prerequisites require a fresh supported manifest, a claimed origin match, declarations of explicit invocation and no content-triggered execution, and the single status file passing the listed checks while reporting `operational`. This is an explicit illustrative triage policy; it does not define minimum evidence for the ATM specification or substantiate those safeguard declarations.

Schema validity and authenticity are separate output fields. Operational-status and platform-control authentication remain separate. Requested detached checks update `manifest.authentication` to match the additive `manifest_authentication.state` result. A claimed revocation label is not a revocation check; `revocation_checked` remains false.

## Draft platform-control checks (report version 0.2)

The [unreleased profile](../../spec/platform-controls-draft-0.1.md) adds explicit platform subject types, deployment/tenant/surface/policy scope, role separation and capability conditions without changing the v0.2.0 schemas. Run its fictional positive case:

```bash
.venv/bin/python tools/consumer/consume.py \
  --manifest examples/consumer/platform-controls/manifest.json \
  --expected-origin https://consumer-demo.example \
  --status-file examples/consumer/operational-status.json \
  --platform-profile-file examples/consumer/platform-controls/profile.json \
  --expected-context-file examples/consumer/platform-controls/expected-context.json \
  --at 2026-10-06T18:00:00Z
```

The operator selects the expected context independently; it cannot be derived from the sidecar as authority. The explicit file is discovered via the manifest's existing `platform_policy` link, but never fetched. Its reference, digest and publication/expiry must match. The profile binds separately to publisher, subject and manifest version; the selected capability and assessment must exactly match platform type/ID, deployment, tenant, surface and policy version. The assessment also repeats the declared control authority, enforcement point and complete capability conditions; a stale snapshot cannot silently cover changed roles or requirements even when the policy version is reused. This experimental profile supports no scope inheritance. Wrong types/scopes, stale input or changed expected policy produce explained `hold`/unresolved output.

`platform_controls.capability` displays declared access conditions and `approval_required`. Listing a capability does not guarantee caller eligibility, and `approval_required` does not imply `approval_granted`. An agent/operator authorization cannot override platform refusal or additional approval. The consumer does not accept agent mandates or invoke capabilities. `policy.caller_eligibility` stays `unresolved`; `access_granted`, `approval_granted` and `runtime_enforcement_performed` stay false.

Missing or malformed requested sidecar/context files produce a source-specific unresolved reason while preserving independently inspected manifest/status results.

A successful `platform_controls.declaration_checks_passed` means only that the local checks matched. Authentication, actual safeguards and revocation remain unverified, and the best decision remains `manual_review`. Missing/stale input leaves capability existence unresolved rather than absent. Without the optional paired profile/context inputs, `platform_controls` reports `profile_not_supplied` and the original demo still checks its narrow legacy status profile. Legacy status subjects must now be exactly the expected platform `id` and `type`, with unsupported qualifiers rejected; publisher and subject equality in that old profile is a supported-demo restriction, not a general ATM identity rule.

The profile checks policy change only against the separately supplied expectation. It cannot discover an undisclosed live deployment/policy change or evaluate the caller's real eligibility. The platform must independently enforce its current policy at invocation. See the [acceptance matrix](../../examples/consumer/platform-controls/cases.json) and [profile limitations](../../spec/platform-controls-draft-0.1.md).

## Network and resource boundary

- HTTPS only, standard port 443, no origin paths, user information, query strings or fragments. ASCII DNS names or public IP literals only.
- DNS answers must all be public unicast addresses; private, local, shared, reserved, multicast, IPv4-mapped/6to4/Teredo and mixed public/private answers are refused. Up to 16 answers are accepted, and only the first is attempted.
- The connection uses the checked address without a second DNS lookup and keeps the requested hostname for TLS certificate verification. Redirects are refused, including redirects to another public host.
- One credential-free GET; no proxy environment, cookies, authorization headers, evidence fetching or caller-supplied schemas are used.
- The response must be HTTP 200 `application/json`, uncompressed, and at most 64 KiB. Ambiguous length headers are refused. Standard-library HTTP header limits apply.
- The isolated fetch worker has an eight-second elapsed-time timeout, with three-second socket timeouts. It is killed and reaped on timeout; there are no retries.
- Local and fetched JSON are capped at 64 KiB, 16 nested levels, 2,048 values, 128 elements per array, 2,048 characters per string and 256 per key. At most 32 artifact references are inspected. These are consumer limits, not schema changes.

Network-boundary tests use controlled transports and DNS answers; no live third-party endpoints are exercised by the test suite. TLS uses the machine's default certificate trust; this is not publisher-signature, key-revocation or verifier-credibility validation.

## Explicit limitations

The structural validator defaults to not enforcing JSON Schema format annotations; its optional `--strict-formats` mode adds format checks independently of this consumer. The consumer separately checks only timestamps it uses, accepting a conservative RFC3339 subset with up to six fractional digits, valid numeric offsets, and no leap seconds or unknown `-00:00` offsets. It does not claim full format or specification conformance.

Without the separately selected detached profile, this original demonstration performs no signature verification. Live safeguard tests, deployment attestation, tenant/surface authorization, issuer registry, independent-verifier discovery, reputation scoring and authoritative finding-revocation checking remain unimplemented. Other evidence is inventoried only. Cache TTLs are displayed in the input artifacts but not enforced; this profile uses explicit expiry without an independent maximum-age policy. Machine clock accuracy is assumed.

Missing or unsupported evidence remains unresolved. Further policy choices are captured in the [review questions](../rfc/0001-consumer-policy.md), not silently treated as standards requirements.

Implementation references: Python's [HTTP client](https://docs.python.org/3/library/http.client.html), [default TLS context](https://docs.python.org/3/library/ssl.html#ssl.create_default_context), and [subprocess timeout behavior](https://docs.python.org/3/library/subprocess.html#subprocess.run).

## Separate protocol-support illustration

External mechanism support is declared in a [new companion schema](../../spec/protocol-support-draft-0.1.md), rather than added to this consumer's existing platform-control profile. The published consumer and both existing draft schemas are preserved. A [non-normative offline reader](../protocol-support-consumers.md) demonstrates how a separate consumer might display support and requirement groups. It implements no protocol payloads, provider fetching, caller authorization or runtime enforcement; its vocabulary and triage choices are illustrative.

## Declared findings versus unresolved evidence

The additive `platform_controls.declared_assessment_result` field reports a current, scope-matched declared `pass`, `fail` or `unknown`; otherwise it is `null`. It never authenticates a finding. Existing reasons and hold/manual-review behavior are preserved. See the [issue #1 decision record](../rfc/0001-consumer-policy-resolution.md).

## Optional detached authentication and finding inputs

The [signing v1 demonstration](../../examples/signing/README.md) adds
`manifest_authentication` and `assessor_finding` without changing the existing
triage decision or platform-controls snapshot rules. Explicit offline files
provide payload/signature/JWKS snapshots. `--authenticate-manifest` in network
mode permits two additional fixed same-origin requests: the signature and
public keys. All original address, TLS, redirect, encoding and time bounds
apply separately, with 4 KiB signatures and 16 KiB JWKS. Assessor findings
are offline only, with at most eight visitor-selected assessor origins.
No generic `report_uri` or evidence-selected key URL is fetched.

Only signature HTTP 404 reports `unsigned`; unavailable endpoints and other
HTTP failures report `unverified`, while malformed/incorrect signatures report
`invalid`. An offline absent file is not confirmed remote absence. Key status
is checked from the selected current-window snapshot; revoked/compromised keys
are unusable even for backdated signatures. Stale/offline snapshots can miss
newer revocations. There is no finding revocation/status implementation.

Authentication attributes bytes to an origin-bound key, applicability checks
typed claims, subject, digest and current observation windows, and acceptance
uses the visitor's chosen assessor. A different origin's self-declared
`independent` relationship stays `independence: unproven`. Access/approval
remain false. `policy.reasons` now reflects the optional checks: publisher authentication
removes `issuer_authentication_unverified`; an accepted finding adds
`claim_accepted:/interaction_profile/explicit_invocation_required` and replaces
the blanket claim reason with `other_claims_without_accepted_findings`.
`policy.claim_acceptance` lists the four interaction-profile pointers separately;
only the assessed claim becomes `accepted_for_claim`, and the other three stay
`unresolved`. Acceptance does not prove organizational independence.
`revocation_not_checked` still concerns the separately supplied operational-status
evidence; it does not say that the selected signing JWKS was ignored. Other
hold reasons remain in force, and no accepted finding changes a hold into approval.
Consumer exit 0 still means manual review, even if optional authentication
failed. It is not an authentication success flag.
