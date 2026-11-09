# ATM v0.2.0 draft documentation

[Repository overview](../../README.md) · [Proposed roadmap](../../ROADMAP.md)

These pages navigate the v0.2.0 draft schemas and specifications. The reference consumer and this documentation are post-prerelease additions; they are not in the original `v0.2.0` source archives. No website deployment or ownership of `agenttrustmanifest.org` is implied. Schema URLs are identifiers resolved locally by the tools.

## Read and try

1. [Core manifest](../../spec/manifest-spec.md): declarations, artifact references, issuer hints and responsibility labels.
2. [Verification](../../spec/verification-spec.md), [reputation](../../spec/reputation-spec.md), and [attestation](../../spec/attestation-spec.md): evidence models and consumer responsibilities. Verification and attestation retain v0.1.0 document versions.
3. [Worked fictional example](worked-example.md): compare exact status bytes with a manifest digest, then observe a decision that grants no access.
4. [Reference consumer](consumer.md): supported inputs, states, limits and network boundary.
5. [Design-review questions](../rfc/0001-consumer-policy.md): scope, freshness, failure behavior and issuer trust remain review topics.

## Schemas

- [Core manifest](../../schemas/agent-trust-manifest.schema.json)
- [Verification report](../../schemas/verification-report.schema.json)
- [Reputation feed](../../schemas/reputation-feed.schema.json)
- [Attestation envelope](../../schemas/attestation-envelope.schema.json)
- [Capability catalog](../../schemas/capability-catalog.schema.json)
- [Operational status](../../schemas/operational-status-feed.schema.json)
- [Revocation feed](../../schemas/revocation-feed.schema.json)

## Project guidance

[Contributing](../../CONTRIBUTING.md) · [Security reporting](../../SECURITY.md) · [Versioning](../../governance/VERSIONING.md) · [Threat model](../threat-model.md) · [Key management](../key-management.md)
