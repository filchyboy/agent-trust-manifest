# Fictional signing and assessor demonstration

All keys, domains and findings here are fictional. The private seeds published
in `vectors.json` are public test material. NEVER use them as operational keys.
The signatures are real test-vector signatures, not evidence that the fictional
assessment happened. Observation labels describe the fixture, not live testing.

The final manifest links a stable assessor finding ID. The assessor finding
then binds the digest of those manifest bytes, avoiding a circular hash.
`report_uri` only discovers a report; a link does not authenticate the assessor.

From the repository root, with Python 3.11.18 and project requirements installed:

```sh
python examples/signing/generate.py
python tools/signing/check_vectors.py
node tools/signing/interop.mjs
python tools/signing/cli.py verify --payload examples/signing/manifest.json \
  --signature examples/signing/manifest.jws --jwks examples/signing/publisher.jwks.json \
  --origin https://consumer-demo.example --type manifest --at 1791309600
python tools/consumer/consume.py \
  --manifest examples/signing/manifest.json \
  --expected-origin https://consumer-demo.example --at 2026-10-06T18:00:00Z \
  --status-file examples/consumer/operational-status.json \
  --manifest-signature-file examples/signing/manifest.jws \
  --manifest-keys-file examples/signing/publisher.jwks.json \
  --finding-file examples/signing/finding.json \
  --finding-signature-file examples/signing/finding.jws \
  --assessor-keys-file examples/signing/assessor.jwks.json \
  --assessor-origin https://assessor.example \
  --trusted-assessor https://assessor.example
```

Expected: manifest authentication `authenticated`; finding authentication
`authenticated`, applicability `matched`, acceptance `accepted_for_claim`,
independence `unproven`. Existing consumer policy stays `manual_review`;
access and approval remain false, operational status remains unverified.
The policy explanation removes the stale issuer-authentication reason and
names only the accepted claim. `policy.claim_acceptance` leaves all other
interaction claims unresolved; independence remains unproven. Removing the
visitor-selected trusted assessor leaves acceptance unresolved.
Altering even manifest whitespace invalidates its signature and finding digest.

For real signing, supply a separately generated secret raw 32-byte Ed25519
seed file and explicit bounded NumericDate window to the offline CLI:

```sh
python tools/signing/cli.py sign --payload manifest.json --seed-file private-seed.bin \
  --origin https://publisher.example --type manifest --kid rotation-1 \
  --iat 1791306000 --exp 1791313200 > manifest.json.jws
```

Protect the seed file with local permissions and use an appropriate key custody
system; this CLI does not generate keys, manage secrets or implement an HSM.
Never publish the seed. Signature output has no final newline. Verification
returns exit 0 only on authentication success; failure returns 1 and a JSON
reason on stderr. Consumer exit codes retain their existing policy meaning
(`manual_review`: 0; `hold`: 1), and are not an authentication-success flag.
Read the separate authentication/applicability/acceptance fields.

Network manifest authentication is optional:

```sh
python tools/consumer/consume.py --origin https://publisher.example --authenticate-manifest
```

This performs up to three fixed same-origin bounded requests. It retrieves no
finding, generic `report_uri`, or report-selected key URL. Signature 404 alone
is `unsigned`; errors are `unverified`, malformed signatures are `invalid`.
Offline files are visitor-supplied snapshots: provenance and latest-key status
are assumptions, not proven by a self-declared origin. `--at` is fixture-only
and forbidden for network mode; a historical clock does not establish
historical validity of a key that is currently revoked.

`vectors.json` contains exact protected objects, signing input hex, public
seeds, signature hex and SHA-256 values. `generate.py` deterministically
reproduces the artifacts. `interop.mjs` independently assembles the JWS signing
input, verifies with Node's standard `crypto`, rejects tampering, and signs
again. Python tests verify those Node-produced signatures. Node is used for
shared-vector interoperability only; it is not a full hostile-input profile
verifier or a second relying-party implementation. General verification uses
the restricted Python wrapper and the pinned PyCA primitive.

The portable corpus also exports **39 negative cases**, each with a stable `id`,
a `base_vector` naming a positive vector's payload filename, exact `overrides`,
and an `expected_reason`. Start each case from its named base, then replace only
specified inputs: `payload_hex`, `signature_hex` and `jwks_hex` are complete raw
byte strings in lowercase hex; `origin`, `type` and `now` replace verifier
expectations. Cases are independent, not cumulative. No Python mutation code
is needed to consume them. Expected reasons are the reference verifier's
specific rejection diagnostics; another implementation can map its own
corresponding failures, but must reject each case.

`check_vectors.py` runs all two positive and 39 negative cases through the
Python profile verifier. The four cases marked `independent_crypto: true`
change only signed bytes, signature bytes or a public key and are also consumed
and rejected by Node's independent standard-crypto path. The original harness still limits itself to those four primitive cases. The
separate [independent Node prototype](../../tools/independent-verifier/README.md)
now checks all 39 negative cases for DNS origins, including parsing and metadata. This is shared-vector cryptographic
interoperability, not a complete second implementation of the profile or its
finding-reliance policy. The existing finding applicability tests remain in
the Python suite.

Imports use the `tools` package and shared offline origin rules. Existing direct
script commands remain supported from other working directories; from the
repository root, `python -m tools.signing.cli` and
`python -m tools.signing.check_vectors` are also supported.

Profiles: [signing](../../spec/signing-profile-v1.md),
[finding](../../spec/finding-profile-v1.md). Neither tooling nor profile requires
a specific assessor. The HTTPS-origin publication option in RFC 0003 remains
valid; business ratings and existing assessed-controls snapshots are unchanged.
