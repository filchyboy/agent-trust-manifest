# Independent DNS-origin signature verifier prototype

This is a separate JavaScript implementation of the v1 signature checks. It
imports neither the Python production verifier nor the older Node vector
harness, invokes no Python process, performs no network operations and fetches
no keys. It verifies exact bytes with Node's standard Ed25519 crypto API.

## Run

Use Node 22 or later. Install the one pinned parser dependency locally from the
lockfile, with package scripts disabled:

```sh
npm ci --ignore-scripts --prefix tools/independent-verifier
npm test --prefix tools/independent-verifier
node tools/independent-verifier/cli.mjs \
  --payload examples/signing/manifest.json \
  --signature examples/signing/manifest.jws \
  --jwks examples/signing/publisher.jwks.json \
  --origin https://consumer-demo.example --type manifest --at 1791309600
```

`--type` is `manifest` or `finding`. `--at` is an offline fixture time; omit it
for the current clock. Local files are bounded before parsing. Exit 0 means
signature authentication, and exit 1 means unverified/rejected input, with a
JSON reason on stderr. No result grants access or proves a claim's truth.

`npm test` runs seven parser, key-lifecycle and CLI test groups, then executes
both positive and all 39 negative shared vectors. Unlike the old primitive
harness, this verifier checks the protected profile/type/origin, lexical integer
dates, JSON and base64 rules, public-only unique-kid JWKS, compromise/retirement
semantics and current validity windows before signature verification.

## Exact scope

- Canonical **DNS origins only**. Public and private IP literals both fail closed
  with `unsupported_ip_origin`. General public-IP origin conformance remains
  outstanding; no DNS request is made even for a DNS origin.
- Signature authentication for both payload types. It does **not** implement
  finding-schema validation, claim/subject/digest applicability, assessor
  relationship investigation or relying-party acceptance. A finding signature
  authenticates that finding's bytes; it does not accept the assessed claim.
- Explicit offline JWKS provenance is supplied by the operator. The program
  cannot establish that the snapshot is the latest origin-published key set.
  It does enforce v1 freshness/expiry and rejects revoked/compromised keys even
  if their signatures claim an earlier issue time.
- This is an additional implementation, not an independent organizational audit,
  a complete second ATM consumer, or a conformance certificate. Passing a finite
  corpus does not establish correctness for all hostile inputs.

## Parser and cryptographic sources

The MIT-licensed [Microsoft JSON parser](https://github.com/microsoft/node-jsonc-parser)
is pinned to `jsonc-parser@3.3.1`. Its parser can recover from errors, so this
wrapper requires an empty error list, disables comments/trailing commas/empty
content, checks duplicate names and bounds, and retains numeric token spelling
so `1.0`, `1e0` and `true` cannot become integer NumericDates. AST objects are
converted into null-prototype data objects; prototype-looking keys stay data.
The lockfile records the package integrity digest; no custom parser or
cryptographic primitive is introduced.

Node's [crypto verification API](https://nodejs.org/docs/latest-v22.x/api/crypto.html#cryptoverifyalgorithm-data-key-signature-callback)
uses an Ed25519 public key with a null algorithm argument as required by that
API. The wrapper separately requires the fully specified protected JOSE
identifier `Ed25519`. Both the existing production wrapper and Node may use
OpenSSL internally; this is independent profile logic, not a claim of unrelated
underlying cryptographic codebases.
