# Reputation Extension Specification v0.2.0

## 1. Purpose

The reputation extension provides time-based and observer-based trust signals about the identified subject at the declared scope. The subject may be a platform or tenant; it is not necessarily the manifest publisher or the reputation provider.

## 2. Design constraints

Reputation should be:
- dimension-specific
- evidence-oriented
- resistant to Sybil amplification
- degradable over time

Dimension-specific reporting is preferred where the assessment actually supports those dimensions. An overall-only business rating may use an empty `dimensions` array; do not fabricate a technical-control dimension merely to populate it. A consuming profile may require dimension-specific evidence for its own use case.

## 3. Recommended dimensions

- `declaration_accuracy`
- `execution_safety`
- `provenance_quality`
- `policy_reliability`
- `incident_responsiveness`
- `stability`

## 4. Feed model

The core manifest should reference an external reputation feed rather than embedding full reputation history. A tenant-scoped feed must identify the relevant tenant subject and scope without implying that its rating applies to other tenants or to the hosting platform. The current schema carries these declarations but does not authenticate their identities or establish scope inheritance.

The original third-party assessment is issued by its reputation provider. A normalized feed may be issued directly by that provider or by a separately identified adapter, including a host adapter. The adapter issues and authenticates its transformation; it does not inherit the original assessor's independence or signature. Neither representation should contain the hosting platform's acceptance decision. Platform acceptance belongs in platform-owned trust state or an attestation acceptance artifact that references the reputation feed hash.

Feeds should disclose:

- issuer
- subject
- scope
- methodology
- dimensions
- evidence references
- assurance level
- revocation status
- signature metadata

## 5. Flexible scoring

Providers may use numeric scores, categorical ratings, pass/fail/mixed results, or a combination, as long as the methodology and scale are disclosed. ATM does not require one universal reputation methodology.

### Provider-native values and normalization

The schema's rating and dimension vocabularies remain bounded. A provider-native grade such as `A+` can be mapped to an existing ATM enum such as `excellent` under an explicitly documented, versioned methodology. This is not a universal equivalence. Preserve the source-native value and source/mapping provenance through referenced provider evidence; the generic ATM validator need not understand every raw provider format. `methodology.rating_scale` does not override the allowed `rating` enum.

The party publishing the normalized feed is responsible for its representation. If an adapter transforms another provider's data, identify the adapter as the transformed feed's issuer and preserve the original statement separately; an original signature does not authenticate changed bytes. Do not map a broad business grade into a technical-control dimension it does not assess. Unmapped values should remain unknown or omitted under the declared policy, not become favorable by default.

See the [schema-compatible fictional example](../examples/rating-normalization/README.md) and [proposed third-party/host lifecycle design](../docs/rfc/0002-third-party-claims-and-host-lifecycle.md). Neither changes the current schemas or implements a ratings integration.

## 6. Operational status

First-party operational status should be published as an `operational_status_feed`, not as reputation. Reputation providers may cite operational status when evaluating dimensions such as `incident_responsiveness` or `stability`.

## 7. Report weighting

Implementations may weight reports using validator standing, attestation quality, historical accuracy, and recency.
