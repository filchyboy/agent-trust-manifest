# Verifier evolution: timing, independent implementations and conformance

Status: decision brief and local prototype, **not a normative profile revision**.
Current `atm-detached-jws/1` and `atm-invocation-finding/1` rules remain unchanged.
No release, tag, merge, branch deletion or deployment is authorized by this brief.

## Confirmed review findings and completed corrections

The consumer's stale authentication explanation was reproducible. PR #9 fixes
that explanation and reports acceptance per claim; accepting the invocation
claim does not accept the other controls or prove assessor independence. It
also exports 39 negative cases, verifies findings once, caches trusted local
schemas and removes consumer/signing sibling import coupling.

The review's count of 30 CI validator steps meant 30 total run steps; 26 were
validator invocations. PR #9 adds the portable corpus step. This distinction
matters when reporting exactly what was tested, rather than treating a setup
or test-suite command as an additional schema check.

## 1. Time limits are different policy dimensions

| Dimension | V1 | Consequence of relaxing it |
| --- | --- | --- |
| JWKS snapshot freshness | At most 24 hours, plus signature/key checks | A new fetch can still return a cached old snapshot; offline copies can miss compromise until expiry |
| Manifest signature lifetime | At most 24 hours | Longer-lived signed bytes can be replayed for longer, even when not the currently deployed document |
| Finding observation-to-expiry interval | At most 24 hours | A longer interval can leave a withdrawn or obsolete finding apparently current without an authoritative finding-status mechanism |
| Manifest digest applicability | Exact full bytes | Every refresh invalidates this particular finding binding, regardless of a longer signature lifetime |
| Assessor observation age | Bounded indirectly by the finding interval | Long-lived audit reports need a separate visitor-selected maximum observation age and a defined scope |

**Recommendation:** keep v1 interoperable and draft a separately identified v2
or a new audit profile before loosening these rules. Do not change v1 constants
while continuing to claim unchanged v1 behavior.

A candidate could bound the manifest signature by the manifest's own expiry,
and a finding signature by the finding's expiry, while requiring the visitor
to select maximum signature and observation ages. These are upper bounds, not
a claim that an issuer-selected expiry alone establishes acceptable currency.
No production defaults for those maxima are selected here. A static audit and
a claim about current invocation behavior need different policies.

Changing only the 24-hour cap will not solve long-lived audit applicability:
this finding profile binds the entire manifest, and new manifest bytes require
new findings. Existing `assessed_controls` scoped snapshots remain an additive
alternative in their own draft; they must not be replaced by full-manifest
binding. A future audit-specific profile needs explicit snapshot scope,
versioning and status/supersession semantics.

Daily signing is operationally restrictive, but it does not require exporting a
hardware-protected key or placing the key in an application process. Hardware
custody, scheduled signing and public key publication are separate choices.

For every candidate, revoked/compromised keys remain unusable for current
assurance regardless of signed iat. No backdated historical exception or
finding-revocation capability is introduced by a longer lifetime.

## 2. Clock tolerance requires a coherent comparison matrix

V1's zero-skew rule is intentional, but operationally unforgiving. A useful
candidate is a **60-second future-issuance tolerance with no expiry grace**.
That candidate needs coordinated rules, rather than a one-line iat patch:

| Check | Candidate treatment requiring profile review |
| --- | --- |
| Manifest published_at, JWKS issued_at, signature iat | No more than 60 seconds ahead of the verifier's clock |
| Finding observation end and issued_at | Same bounded future allowance, while preserving start <= end <= issued_at |
| Key nbf versus signature iat | Preserve signed-order binding nbf <= iat; do not silently accept a signature issued before key validity |
| Retirement cutoff | Specify how the same clock tolerance affects a cutoff declared by the issuer; never treat compromise as retirement |
| Manifest/JWKS/key/signature/finding expiry | Always now < expiry, with no post-expiry grace |
| Every interval | Preserve strict positive duration and typed integer NumericDates |

No such tolerance is implemented in the current v1 verifier or the independent
prototype. If chosen, it needs shared vectors for every boundary, including
59/60/61 seconds, exact expiry, cross-clock observation order, retirement and
revoked backdated signatures. Clock tolerance is not trustworthy timing proof.
Do not fabricate observation timestamps or advise arbitrary backdating as a
substitute for clock synchronization.

## 3. Independent implementation milestone

The separate [Node prototype](../../tools/independent-verifier/README.md) now
checks both positive and all 39 negative signing vectors independently of the
Python verifier, including parsing, protected metadata, public JWKS and key
status. It adds seven parser/lifecycle/CLI test groups and uses a pinned parser
plus Node's standard crypto implementation.

This advances signature-profile interoperability beyond the original four
primitive-negative checks. It does not complete the roadmap's broader second
consumer:

1. Specify and test public-IP origin equivalence; the prototype rejects all IP
   literals and is explicitly DNS-only.
2. Export finding-applicability vectors for typed values, exact subjects,
   observation windows, manifest refresh, unselected assessors and publisher
   self-assessment, with expected authentication/applicability/acceptance states.
3. Implement those finding checks independently and preserve unresolved truth,
   organizational independence and access decisions.
4. Obtain review or replay by another implementer; multiple implementations in
   one project are not themselves an independent assessment of the protocol.

No network fetching or finding lifecycle is hidden inside the new prototype.
Offline snapshot provenance remains an explicit operator assumption.

## 4. Documentation and normative/default choices

The README should be a navigation and quick-start document. Current profile
status, trust roles, one setup path and links belong there; detailed compatibility
history belongs in the changelog, and runtime remediation history in the
contributor guide. Existing note URLs can remain redirect stubs so useful
history and links are preserved without maintaining duplicate narratives.

Keep structural validation as the existing CLI default. Recommend
`--strict-formats` explicitly for authoring and CI where formats matter; a
default switch would be a documented compatibility change. Format checks still
cannot authenticate an issuer or establish current evidence applicability.

Adding RFC 2119 words to older documents is not automatically a harmless style
edit. First identify which existing assertions become testable requirements,
the affected version/conformance class, compatibility effects and coverage.
The newer optional profiles already use normative language. A release proposal
can distinguish them from the core draft and companion experiments without
silently declaring the entire repository production normative.

## Decisions to resolve next

- Choose an audit-specific scoped profile versus extending the full-manifest
  invocation profile; select visitor age bounds with an actual operational use
  case and finding-status expectations.
- Accept or reject the coordinated 60-second future-only tolerance in a new
  profile identifier; preserve exact expiry and compromise handling either way.
- Complete the independent consumer acceptance matrix before claiming that
  milestone complete. Keep strict-format and release-default changes explicit.
