# Worked example: declared status, checked bytes, unresolved trust

[Documentation index](index.md) · [Consumer contract](consumer.md)

Every identity and hostname here is fictional. The `.example` origin is not a deployed endpoint. The demonstration is entirely offline and uses a fixed decision time so it remains repeatable after its historical timestamps expire.

## 1. Read the artifacts

The [manifest](../../examples/consumer/manifest.json) claims that consequential actions require explicit invocation and that content alone cannot trigger execution. It references one [operational-status feed](../../examples/consumer/operational-status.json), maintained by the fictional `example_status_team` role, and declares that feed's exact SHA-256 byte digest.

The status feed says `operational`. Neither statement has been independently tested. The manifest and status identify the same fictional platform scope; the owner label grants no authority.

## 2. Run the consumer

After the [isolated setup](../../README.md#quick-start), run from the repository root:

```bash
.venv/bin/python tools/consumer/consume.py \
  --manifest examples/consumer/manifest.json \
  --expected-origin https://consumer-demo.example \
  --status-file examples/consumer/operational-status.json \
  --at 2026-10-06T18:00:00Z
```

Key output fields:

```json
{
  "manifest": {"state": "fresh", "authentication": "unverified"},
  "status_evidence": {
    "state": "unverified",
    "digest": "matched",
    "schema": "valid",
    "status_freshness": "fresh",
    "revocation_checked": false
  },
  "policy": {"decision": "manual_review", "access_granted": false}
}
```

This is an excerpt, not the whole report. The hash comparison is the demonstrable evidence check: these status bytes match what this manifest names. The policy still lists issuer authentication, independent assessment and revocation as unresolved. It does not authorize an interaction or establish that any safeguard works.

## 3. Exercise failures

Substitute `examples/consumer/stale-manifest.json` for the manifest. The manifest is `stale`, the decision is `hold`, and the process exits 1.

Substitute `examples/consumer/tampered-status.json` for the status file. That structurally valid file has different bytes and reports `degraded`; the original manifest's digest no longer matches. The consumer reports `status_digest_mismatch` and holds.

Omit `--status-file`. The reference is visible but the selected evidence is `missing`; it is never fetched automatically. The decision is `hold`.

Malformed JSON, missing required fields, inconsistent timestamps, cross-origin references and unsupported tenant/surface scopes are also held. The [tests](../../tests/test_consumer.py) cover these cases, private addresses, redirects, size limits and fetch timeouts.

## 4. Identify what remains to be decided

An independent verifier would need a documented method for checking the actual invocation and execution controls. A relying party would need an issuer-trust and revocation policy, a scope model and minimum evidence requirements. A matching digest or a claimed `pass` result does not replace that work. See the [focused RFC questions](../rfc/0001-consumer-policy.md).
