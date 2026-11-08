# Fictional provider-native rating → ATM-compatible feed

This example is not a BBB integration and does not describe BBB's methodology. All sources, grades, identities and signatures are fictional. It demonstrates how a provider can map its native vocabulary to the existing ATM schema rather than requiring ATM to accept arbitrary raw formats.

- `provider-native.json`: an external provider's invented raw format. It is **not** an ATM document and is not validated against the reputation schema.
- `mapping.json`: a fixture-only, versioned mapping record, **not** a proposed ATM wire format or a production adapter.
- `normalized-feed.json`: the provider's ATM-compatible representation. Native `A+` becomes `overall.rating: excellent` under this provider's disclosed mapping. `dimensions` is empty because a broad business grade does not prove a particular technical-control dimension.

The normalized feed's issuer is the same fictional party that issues the native observation. The mapping version, methodology location, native evidence URI and exact source-byte digest preserve the route back to what was mapped. A production provider must authenticate the representation and its relevant bindings according to the applicable profile; putting an issuer name and digest in JSON does not do that.

`methodology.rating_scale` lists the allowed normalized interpretation, not permission to put arbitrary strings into `rating`. The example mapping is provider-specific and lossy. An unmapped native value yields `unknown`, not a favorable grade. Visitors decide whether they trust the provider and the mapping; equal normalized labels from different providers need not imply equal methodologies or evidence.

If an adapter rather than the provider produces this feed, it must name itself as the transformed feed's issuer and retain the original provider's statement separately. A signature on the raw source cannot authenticate transformed output. That adapter-authored variant is a design case, not implemented here.

The schema requires signature metadata, so this fixture includes an explicit non-signature placeholder and declares only `assurance_level: declaration` and `revocation_status: unknown`. Structural validity is not cryptographic validity. No grading, authentication, publication or notification actually occurs.

Schema check with the repository's optional validator:

```bash
.venv/bin/python tools/validator/validate.py examples/rating-normalization/normalized-feed.json schemas/reputation-feed.schema.json
```

Offline consistency checks:

```bash
python3 -m unittest discover -s tests -p test_rating_normalization.py
```

See the [design proposal](../../docs/rfc/0002-third-party-claims-and-host-lifecycle.md) for trust decisions and host lifecycle behavior.
