# External consumer illustration for protocol-support declarations

The [protocol-support companion](../spec/protocol-support-draft-0.1.md) is a schema/specification. It does not implement protocols, runtime authorization or enforcement. This page and `tools/consumer/illustrate_protocol_support.py` are explicitly **non-normative**, bounded offline examples of how another implementation might read its declarations. They neither change the existing reference consumer nor define mandatory ATM policy decisions.

## Fictional configuration and discovery

The fixture describes a tenant administrator's declaration for one concrete platform, deployment, tenant, HTTPS surface, capability and policy version. It offers two fictional recognition alternatives and one fictional payment method, with explicit specification/version/profile tuples. The map and groups could be emitted from administrator configuration; no administration product or protocol adapter is implemented here.

[The example ATM manifest](../examples/consumer/protocol-support/manifest.json) discovers [the companion](../examples/consumer/protocol-support/declaration.json) through an ordinary `platform_policy` reference. A real consumer must separately validate the manifest relationship, publisher authority, subject, scope, integrity and freshness. This reader accepts an explicit local companion file; it neither fetches the discovery link nor authenticates it. `manifest_binding_checked` remains false.

## Try the offline illustration

Use an existing Python environment with the repository's documented `jsonschema` dependency:

```bash
python tools/consumer/illustrate_protocol_support.py \
  --declaration-file examples/consumer/protocol-support/declaration.json \
  --expected-context-file examples/consumer/protocol-support/expected-context.json \
  --known-vocabulary-file examples/consumer/protocol-support/known-vocabulary.json \
  --at 2026-10-06T18:00:00Z
```

The expected context is independently supplied and must match the complete binding exactly. The vocabulary lists fictional protocol/specification/version/profile tuples the demonstration knows how to name. It is not evidence of installed adapters, compatible payload verification or independently tested support. Editing the vocabulary cannot grant access.

## Illustrative outputs and choices

| Output/behavior | Illustration meaning; not mandated schema policy |
| --- | --- |
| `state: declarations_read` | The demo could describe the declarations for the selected context. It is not permission, protocol execution or full specification conformance. |
| `state: unresolved` | The demo could not describe an applicable/understood set because of missing, malformed, stale, mismatched or ambiguous input, or unresolved required mechanisms. Another consumer may choose a hold, deny or additional-review workflow. |
| `vocabulary_match` | An exact tuple appears in the separately supplied fictional vocabulary. It is not an adapter or interoperability test. |
| `requirements[].interpretation` | For one-of, some explicitly supported alternative is in the vocabulary; for all-of, every member is. It does not check a caller's presentation or fulfill a requirement. |
| `independent_testing` | `not_supplied`, or `unverified` when a report is referenced, including a claimed independent report. Reports are never fetched or authenticated. |
| Authority fields | `access_granted`, `approval_granted`, `requirements_satisfied`, `interoperability_verified`, and `runtime_enforcement_performed` always remain false; caller eligibility remains unresolved. |

The false authority/fulfillment fields mean that this reader issued or verified no grant, approval or requirement fulfillment; they do not report a live platform denial or a failed transaction.

The reader compares exact tenant/deployment/surface/capability/policy context, rejects ambiguous repeated tuples and dangling requirement keys, and checks its supplied decision time against publication/expiry. Those are bounded demonstration checks, not live platform behavior. It has no endpoint invocation, provider selection, protocol negotiation, credential processing, approval workflow or protocol-specific adapter. The inherited JSON decoder bounds input and rejects duplicate keys; schemas are local and remote references are never loaded.

No listed support or recognized requirement can override a platform refusal, current authorization decision or additional approval. A declaration with no requirements does not prove no real requirements exist. Missing/unknown/stale support stays unresolved rather than being treated as permission or absence. The reader cannot detect undisclosed changes or determine that its independently supplied expectation is current.

Exit 0 means only `declarations_read`; exit 1 means unresolved; argument errors use exit 2. `--at` is an offline fixture clock, not a claim about live availability. The [case matrix](../examples/consumer/protocol-support/cases.json) separately records structural schema validity and this reader's illustrative outcomes. The schema's meanings are defined in the [specification](../spec/protocol-support-draft-0.1.md), not by this executable.
