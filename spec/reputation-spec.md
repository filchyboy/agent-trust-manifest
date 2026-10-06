# Reputation Extension Specification v0.2.0

## 1. Purpose

The reputation extension provides time-based and observer-based trust signals about an ATM publisher.

## 2. Design constraints

Reputation should be:
- dimension-specific
- evidence-oriented
- resistant to Sybil amplification
- degradable over time

## 3. Recommended dimensions

- `declaration_accuracy`
- `execution_safety`
- `provenance_quality`
- `policy_reliability`
- `incident_responsiveness`
- `stability`

## 4. Feed model

The core manifest should reference an external reputation feed rather than embedding full reputation history.

The reputation feed is issued by a third-party or otherwise independent reputation provider. It should not contain the subject platform's acceptance decision. Platform acceptance belongs in platform-owned trust state or an attestation acceptance artifact that references the reputation feed hash.

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

## 6. Operational status

First-party operational status should be published as an `operational_status_feed`, not as reputation. Reputation providers may cite operational status when evaluating dimensions such as `incident_responsiveness` or `stability`.

## 7. Report weighting

Implementations may weight reports using validator standing, attestation quality, historical accuracy, and recency.
