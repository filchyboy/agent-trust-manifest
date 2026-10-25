# External protocol-support declarations — draft 0.1

Status: new, local, unreleased proposal. ATM remains a schema/specification. This companion describes a platform's declared support and requirements for external mechanisms; it does not implement those mechanisms, install adapters, perform negotiation, authorize callers or enforce runtime policy. The [offline reader](../docs/protocol-support-consumers.md) is a separate non-normative illustration of possible external-consumer behavior.

## Purpose and scope

A platform or tenant administrator may configure one or more recognition, authentication or payment mechanisms for publication through ATM. For example, a declaration could identify a reviewed Visa Trusted Agent Protocol specification and its supported revision/profile. That is a support claim, not evidence of an implemented integration. The repository's examples use only fictional mechanisms.

An administrator saving configuration may cause a publisher to emit this document. Configuring a declaration is distinct from installing a protocol adapter, making an endpoint available, granting runtime access or verifying interoperability. This format specifies the public declaration only; it does not prescribe an administration console or private storage model.

Each document has one explicit `applies_to` binding: platform subject type/ID plus deployment, concrete tenant, surface, capability ID and policy version. All mechanisms and groups in that document share exactly that binding. There are no per-entry scope overrides, wildcard scopes, implicit platform-to-tenant inheritance, transitive inheritance or delegated catalogs. A different tenant or capability needs a separately bound document. A platform-wide declaration must not silently satisfy a tenant requirement.

## Discovery and identity

Use the existing core `governance_artifacts` discovery mechanism with artifact `type: platform_policy`, this schema ID and `version: protocol-support-draft/0.1`. [The manifest example](../examples/consumer/protocol-support/manifest.json) links an explicit companion URL; the path is illustrative, not a new mandatory well-known endpoint. Core ATM's abbreviated artifact scope is insufficient to establish every qualifier: the consumer must inspect the companion's full binding.

The companion declares compatible `atm_version: 0.2.0` and the associated `manifest_version`. `publisher.id` and `publisher.role` identify the claimed publishing entity and `platform_operator` or `tenant_operator` role. `control_authority.id` names the claimed party setting policy. The platform subject is separate. A tenant operator can publish only a claim about the document's concrete tenant; its role label neither authenticates tenant administration rights nor establishes authority to override platform policy.

External implementations must establish the publisher's authority and the relationship to the fetched manifest, origin, platform subject, tenant and current policy independently. A matching ID, declared role or digest is not that proof. Existing key/issuer trust and revocation questions remain unresolved; protocol-support declarations do not become agent mandates.

## Mechanism declaration

`mechanisms` is a map of local keys to typed declarations. Keys are document-local references, not globally registered protocol identifiers. Each entry requires:

| Field | Declaration meaning |
| --- | --- |
| `protocol_id` | Stable URI identifier for the external protocol or mechanism; not a transport enum or endpoint. A namespaced identifier does not imply registry approval. |
| `specification_uri` | HTTPS reference identifying the specification whose semantics are intended. |
| `version` | Exact supported external revision. If the source has no formal version, use an explicit reviewed snapshot/revision label and explain it in documentation; do not invent a vendor-issued version. |
| `profile` | Explicit external profile or an explicitly documented base-profile label. No default profile is inferred. |
| `roles` | One or more of recognition, authentication, payment or other. Roles describe this mechanism's use here; they do not classify an entire external project into an exclusive category. |
| `support` | `supported`, `unsupported` or `unknown` for this exact binding/revision/profile. Each is a publisher declaration, not independently tested truth. |

`version` and `profile` are nonblank and reject the ambiguous tokens `*`, `latest`, `current` and `unknown`. An unrecognized revision is still structurally representable; a schema does not maintain the universe of supported external specifications. The complete protocol/specification/version/profile tuple identifies the intended mechanism variant. Different revisions require distinct map entries when advertised together. Duplicate tuples with contradictory declarations are ambiguous and must not silently override one another.

Optional `endpoint_uris` identify configured service endpoints; `documentation_uris` identify implementation documentation. Both remain distinct from `specification_uri`. Do not assume that a specification URL is an invocation endpoint or fetch it as one. References must not contain credentials, bearer capabilities or private policy. Their presence guarantees neither reachability nor caller access.

An optional `test_report` contains a report URI, assessor ID and claimed relationship (`self`, `affiliated`, `independent`, `unknown`). It is a reference to a claim, not a verified test result. External consumers must authenticate the assessor, examine the report's exact applicability/version and freshness, and assess independence before claiming independently tested support. `support: supported` by itself means only declared support; there is no `certified` or `independently_tested` support state.

These fields are distinct from existing `fulfillment.protocol` values such as HTTPS or MCP. A transport identifies how to reach a capability; it does not identify a recognition or payment specification. `auth.context` and free-text access conditions likewise cannot substitute for this typed declaration. External protocol payloads, credential formats and verification procedures remain external.

## Support versus requirements

A mechanism appearing in `mechanisms` is not automatically required. `requirements` explicitly lists requirement groups referencing local mechanism keys:

- `one_of`: at least one listed alternative is required. This is not exclusive XOR; advertising or satisfying more than one alternative is not prohibited by this operator.
- `all_of`: all listed mechanisms are jointly required.
- Multiple groups are jointly applicable: all groups must be satisfied by the real interaction. This permits, for example, one of two recognition methods together with a payment method.

Groups cannot be empty, use unknown operators, or repeat keys within a group. Every referenced key must resolve unambiguously within this document. A supported entry outside every group is optional support. A required entry declared unsupported or unknown is an unresolved condition, not a fulfilled requirement. A dangling key or unknown mandatory mechanism/version/profile must not silently pass. For one-of, an understood applicable alternative may remain usable even when a different alternative is unknown; the unknown branch itself is never considered satisfied. For all-of, one unresolved member leaves the group unresolved.

These are declaration semantics, not an authorization engine. An external implementation determines whether a real caller actually presents and fulfills an accepted mechanism under current platform policy. Discovering a group, recognizing its vocabulary or validating its structure does not satisfy it. Platform refusal or an additional approval requirement remains authoritative. No capability listing or operator authorization overrides it.

## Missing, unknown and stale information

The field `requirements` is required to avoid an accidental default. An explicit empty list means only that this document declares no mechanism requirement; it does not assert the platform has no other conditions. Empty `mechanisms` means no support is described here. An absent document, absent entry, stale declaration or unknown support must remain unresolved, not permission and not proof that the capability or mechanism does not exist.

Freshness, policy changes and evidence applicability remain necessary external checks. A changed tenant, deployment, surface, capability or policy version cannot inherit this declaration. Even unexpired content cannot establish that a live configuration is unchanged. This schema carries publication/expiry metadata but does not implement clock, cache, maximum-age, signature, revocation or availability checks.

## Schema validation and semantic validation

The schema checks types, required fields, enum values, closed objects, explicit bindings, nonempty groups, local-key syntax and declared URI/revision shape. As with the existing validator, URI/date-time `format` annotations alone are not enforced by the repository CLI. Its HTTPS/identifier patterns are structural checks, not URL-safety or authority verification.

Portable JSON Schema does not compare arbitrary external contexts or resolve dynamic map references. Cross-tenant applicability, referenced-key resolution, tuple ambiguity, manifest/publisher binding, freshness and actual requirement satisfaction need separate semantic checks by an external implementation. A structurally valid wrong-tenant declaration is still inapplicable. Tests distinguish schema rejection from the offline illustration's explicitly labelled semantic choices.

## Versioning and migration

Schema ID: `https://agenttrustmanifest.org/schemas/protocol-support-draft-0.1.schema.json`; profile marker: `protocol-support-draft/0.1`. Schema URLs are identifiers resolved locally; hosted availability is not established. The separate vocabulary schema is only for the offline demonstration, not an ATM protocol registry.

The original seven schemas and the already published platform-control draft 0.1/context schemas remain byte-for-byte unchanged. No typed fields are inserted into those closed objects. Older consumers may inventory this new artifact, but must not infer supported or required mechanisms from a profile they do not understand. The existing reference consumer is unchanged and deliberately does not accept this new artifact as its old platform-control profile.

To migrate, publish a separately versioned companion, select an exact subject/scope and declare mechanism tuples/groups explicitly. Do not mechanically turn free-text conditions into support claims or reuse an existing assessment as evidence for new declarations. Keep old artifacts/version markers available where needed; there is no silent downgrade or change to their semantics. Any incompatible evolution of this new draft must use a new profile/schema identifier, and any future core change requires separate versioning review.
