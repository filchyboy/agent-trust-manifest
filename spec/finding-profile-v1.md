# Invocation finding profile v1

Status: optional normative profile `atm-invocation-finding/1`, limited to the
platform claim `/interaction_profile/explicit_invocation_required`. The third
party is responsible for its assessment; the visitor chooses which assessors,
methodologies and evidence to accept. This fictional demonstration performs no
live assessment and creates no partnership or integration.

The JSON object MUST have exactly these members; its detached signature uses
[signing profile v1](signing-profile-v1.md), type `application/atm-finding+json`,
and assessor origin/key binding:

| Member | Constraint |
| --- | --- |
| `profile` | `atm-invocation-finding/1` |
| `id` | `assessor.origin + /findings/` followed by 1–64 letters, digits, `_`, `-` |
| `assessor` | exactly `origin` (visitor's expected origin) and `relationship` (`independent`, `affiliated`, `self`) |
| `subject` | exactly `origin` (visitor's expected platform origin), `type: platform` |
| `manifest_sha256` | lowercase SHA-256 hex of the full exact manifest bytes |
| `claim` | exactly `pointer: /interaction_profile/explicit_invocation_required`, `value` (JSON boolean) |
| `observation` | exactly integer NumericDates `start`, `end` |
| `issued_at`, `expires_at` | integer NumericDates, identical to signature `iat`, `exp` |
| `method` | `static`, `active`, or `audit` |
| `result` | `pass`, `fail`, or `unknown` |
| `limitations` | nonempty string describing actual assessment limits |

All signing-profile JSON bounds and NumericDate ranges apply.
`start <= end <= issued_at <= now < expires_at` and
`expires_at-start <= 86400` MUST hold. The exact manifest digest, platform
subject and typed asserted value MUST match visitor expectations. JSON `true`
is not integer `1`, and `false` is not `0`. Whitespace, manifest refresh,
version changes, or any other byte change invalidate this full-manifest
binding, even if the single claim value did not change. A matching digest
proves bytes, not publisher authorship: manifest authentication is separate.
Use current structurally valid ATM 0.2.0 manifests before relying on a finding. The demo requires `issuer.uri` to equal the canonical expected platform origin and `issuer.domain` to match its hostname, and requires the current time within the manifest publication/expiry interval.

The reference demo reports three separate results: authentication attributes
the signed finding to the assessor; applicability compares claim, bytes,
subject and times; acceptance applies the visitor's bounded explicit assessor
selection. The demo accepts a supportive `pass` about boolean `true` only
from a selected different-origin assessor declaring `independent`. That
self-declaration and a different domain DO NOT prove organizational independence.
`independence: unproven` stays visible even for accepted findings. Production
visitors choose their own reliance policy and may require relationship
investigation, supporting observations or stricter freshness. Acceptance is
only for this claim within the stated window, never a universal truth verdict,
a deployment guarantee, a tenant decision or an access grant.

A publisher-signed copy, hash pin, link, or endorsement cannot authenticate
assessor issuance. The signature and JWKS must bind to the separately selected
`assessor.origin`; publisher keys cannot substitute. Publisher-origin
self-assessments are not accepted as independent evidence by the demo.
An untrusted assessor can have a mathematically valid signature and a matching
claim, while visitor acceptance remains unresolved.

The stable `id` URL can be placed in generic `verification.verified_by[].report_uri`
before publishing the manifest. Then finalize the manifest bytes, sign them,
and issue the finding over their digest. Serve the finding and its `.jws`
sidecar at that assessor-controlled location; do not hash the finding into
that manifest. This avoids a digest cycle. The URI is discovery only; its
presence or a local file link alone authenticates nothing. The reference
consumer fetches neither URL; the visitor supplies the files and assessor
key snapshot explicitly. A future revision needs a new finding identifier
and updated manifest bytes/signatures as applicable.

This additive profile does not replace existing `assessed_controls` scoped
snapshots or RFC 0003's alternative authenticated-origin publication. It is
not the proposed business-rating or tenant/surface profile. Finding revocation,
supersession/status feeds, transparency, independently timed historical proof,
deployment-bound observations, tenant removal, notifications and access
decisions are out of scope. A signature-valid finding may have been withdrawn
without the offline consumer knowing; expiry and key revocation do not provide
a full finding lifecycle. No assessor trust registry is supplied.
