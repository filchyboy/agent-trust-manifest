# Reference consumer: a bounded demonstration

[Documentation index](index.md) · [Worked example](worked-example.md) · [Design review](../rfc/0001-consumer-policy.md)

The consumer displays four declared interaction controls, inventories evidence, and evaluates one explicitly supplied operational-status file. It is a demonstration profile, not a general trust engine, a conformance certification tool, or a live verifier of the declared safeguards.

## Inputs and commands

Use the Python environment from the [README](../../README.md#quick-start). The existing `jsonschema` dependency provides structural checks; there are no new package dependencies.

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
| `policy.decision: manual_review` | Prerequisites passed; issuer authentication, independent assessment and revocation checks remain unresolved. |
| `policy.access_granted: false` | Neither decision grants access or approves an action. |

Prerequisites require a fresh supported manifest, a claimed origin match, declarations of explicit invocation and no content-triggered execution, and the single status file passing the listed checks while reporting `operational`. This is an explicit illustrative triage policy; it does not define minimum evidence for the ATM specification or substantiate those safeguard declarations.

Schema validity and authenticity are separate output fields. `authentication` remains `unverified`. A claimed revocation label is not a revocation check; `revocation_checked` remains false.

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

The original structural validator is unchanged and still does not enforce JSON Schema format annotations. The consumer separately checks only timestamps it uses, accepting a conservative RFC3339 subset with up to six fractional digits, valid numeric offsets, and no leap seconds or unknown `-00:00` offsets. It does not claim full format or specification conformance.

No signing, signature verification, live safeguard tests, deployment attestation, tenant/surface authorization, issuer registry, independent-verifier discovery, reputation scoring or authoritative revocation checking is implemented. Other evidence is inventoried only. Cache TTLs are displayed in the input artifacts but not enforced; this profile uses explicit expiry without an independent maximum-age policy. Machine clock accuracy is assumed.

Missing or unsupported evidence remains unresolved. Further policy choices are captured in the [review questions](../rfc/0001-consumer-policy.md), not silently treated as standards requirements.

Implementation references: Python's [HTTP client](https://docs.python.org/3/library/http.client.html), [default TLS context](https://docs.python.org/3/library/ssl.html#ssl.create_default_context), and [subprocess timeout behavior](https://docs.python.org/3/library/subprocess.html#subprocess.run).
