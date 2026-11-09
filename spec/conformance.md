# Conformance classes and validation coverage

This document identifies existing contracts; it adds no required core field,
algorithm, enum or universal trust policy. Uppercase requirement words in the
linked normative specifications use [BCP 14](https://www.rfc-editor.org/rfc/rfc8174).
A tool result MUST be described for the actual class/check performed, rather
than promoted into a claim about all ATM behavior or assessment truth.

| Class/check | Existing requirements or scope | Evidence and limits |
| --- | --- | --- |
| Core publisher v0.2.0 | Core schema/required types, RFC 3339 timestamp syntax, applicable extension contracts | `spec/manifest-spec.md` section 7; structural CLI covers schema assertions, strict mode also checks supported format annotations; neither alone establishes all semantic conformance |
| Structural validation | Selected local Draft 2020-12 schema assertions | Default or explicit `--structural-only`; unknown references never retrieve remotely; no cryptographic/current-evidence assurance |
| Format checking | Supported URI/date-time annotations in addition to structure | Explicit `--strict-formats`; all 25 distinct authoring examples now use this mode in CI; not full timestamp/transport/trust conformance |
| Detached signing v1 | Exact bytes, protected profile/type/origin, Ed25519, strict JSON/base64/JWKS and time/key rules | Two positive and 39 negative vectors; Python and independent Node; no statement-truth, deployment or legal identity guarantee |
| Invocation finding v1 | Assessor signature, expected platform subject, pointer and boolean, exact manifest bytes and observation/time bindings | 56 shared offline consumer cases; authentic but wrong-subject/value/stale/unselected evidence remains unaccepted |
| Reference visitor acceptance | Explicit selected assessor, supportive finding, declared relationship and optional stricter observation age | A relying-party example, not a universal assessor list. Independence remains unproven; truth remains unresolved; access remains false |
| Origin handling | Canonical DNS and public-IP literals, rejecting unsafe/special-use addresses | 159 shared cases with boundary sampling; Node's pinned address-policy snapshot matches the selected Python runtime tables, not a claim of exhaustive testing of all addresses |
| HTTP retrieval | Fixed same-origin paths, public-address pinning, TLS, no redirects/proxies and bounded workers | Existing reference Python fetch tests; independent Node consumer is offline and does not claim independent transport conformance |
| Experimental companion drafts | Their own declared subject/scope/control snapshots and semantics | Existing platform-control/protocol-support tests; these do not replace signed finding profiles or receiving-platform enforcement |

## Existing publisher rules versus validator defaults

The core draft's requirements for schema validity, required fields, timestamp
syntax and included extensions are existing conformance requirements; explicit
MUST wording restates them. It does not change the legacy schema permissions
for arbitrary version/algorithm strings or empty placeholder signatures. No
such placeholder becomes authenticated because structural/format checks pass.

Keeping structural validation as the CLI default preserves existing callers.
Authors can opt into strict formats, and CI does so for the complete curated
example catalogue. The catalogue replaces 26 invocations with 25 distinct
fixture/schema pairs because the old workflow checked one pair twice. A future
change to the CLI default would require its own compatibility/version decision.

Older extension design goals and lower-case advice remain guidance unless
an applicable specification/profile makes a specific requirement normative.
This inventory does not retroactively turn every recommendation, lifecycle
proposal or reputation design aspiration into a mandatory protocol feature.

## Responsibility and unsupported claims

Publishers disclose; assessors own their assessments; visiting agents choose
which issuers/evidence to accept. The platform cannot establish substantive
truth or organizational independence by naming, linking, copying, hashing or
signing an assessor's statement. A visitor may rely on an appropriately scoped
authenticated assessor it trusts without repeating the assessment. None of
these checks grants caller permission or replaces runtime enforcement.

V1 time limits and zero skew remain in force. Longer audit lifetimes, a new
clock-tolerant profile, finding status/revocation and deployment-bound proof
remain separate design work. The offline class now has two implementations,
but no independent organizational audit or third-party replay is asserted.
