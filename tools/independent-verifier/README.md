# Independent offline v1 signature and finding consumer

This is a separate JavaScript implementation of the v1 signature checks and
offline finding applicability/visitor-selected acceptance. It
imports neither the Python production verifier nor the older Node vector
harness, invokes no Python process, performs no network operations and fetches
no keys. It verifies exact bytes with Node's standard Ed25519 crypto API.

## Run

Use Node 22 or later. Install the pinned parser and schema-validator dependencies locally from the
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

`npm test` runs 12 parser, key-lifecycle and CLI test groups, then executes
both positive and all 39 negative shared signature vectors, eight shared
authentication outcomes, 56 finding-consumer
cases and 159 origin cases. Unlike the old primitive
harness, this verifier checks the protected profile/type/origin, lexical integer
dates, JSON and base64 rules, public-only unique-kid JWKS, compromise/retirement
semantics and current validity windows before signature verification.

## Finding evaluation and explicit visitor policy

```sh
node tools/independent-verifier/finding-cli.mjs \
  --finding examples/signing/finding.json --signature examples/signing/finding.jws \
  --jwks examples/signing/assessor.jwks.json --manifest examples/signing/manifest.json \
  --platform-origin https://consumer-demo.example --assessor-origin https://assessor.example \
  --manifest-signature examples/signing/manifest.jws --manifest-jwks examples/signing/publisher.jwks.json \
  --trusted-assessor https://assessor.example --at 1791309600
```

The finding CLI separates authentication, applicability and acceptance. Optional
`--manifest-signature` and `--manifest-jwks` inputs also authenticate the same
manifest bytes and report `manifest_authentication` separately; if requested,
that authentication must succeed for exit 0. Publisher failure cannot be
hidden by a valid assessor finding, and publisher success cannot issue an
assessor finding. Without those inputs, only the finding is authenticated. Exit 0
means this one finding was accepted under the visitor's selected assessor and
optional age limit; it is never an access grant. Without `--trusted-assessor`,
authenticated applicable evidence remains unaccepted. The optional
`--max-finding-age-seconds` (0..86400) only tightens acceptance; omission preserves
v1. The signature-only CLI retains its separate signature-authentication meaning.

## Exact scope and interoperability evidence

- Canonical DNS and public IPv4/IPv6 origins are supported. Address
  classification uses `ip-policy-v1.json`, a versioned snapshot of the existing
  Python 3.11.18 reference policy. Shared data is policy, not shared verifier
  code. Native URL/isIP parsing and independent prefix comparisons implement
  the Node path; no DNS request or Python call is made. Updates to the pinned
  runtime's address tables require explicit policy review and differential
  vector updates. This snapshot is not a new universal IP trust registry.
- Finding schema/bindings, exact manifest digest, typed value, subject and
  observation window are checked independently. The core manifest schema is
  validated with pinned Ajv Draft 2020-12 using only repository schemas, no
  remote resolver, no type coercion or default insertion. Format annotations
  are not silently made new assertions; the timestamps/origins used by this
  profile receive their own exact semantic checks.
- Both implementations run 56 shared finding cases and 159 origin cases, in
  addition to two positive and 39 negative signature vectors. Cases cover
  selected/unselected issuers, publisher substitution/self-assessment, wrong
  subject/type/value, stale data, digest refresh, key compromise, exact expiry,
  59/60/61-second future rejection and visitor age boundaries.
- Self-declared independence remains `unproven`, and substantive truth remains
  `unresolved`. The visitor supplies the accepted assessor list; the platform
  neither appoints that list nor makes the assessment true. No retrieval,
  operational-status consumer, deployment/tenant/surface finding or access
  decision is implemented here.
- Explicit offline JWKS provenance remains operator supplied. Snapshot expiry
  and revoked-key rejection do not establish the latest publication or a full
  finding revocation/status lifecycle.
- This is an independent implementation of the bounded offline consumer class,
  not an independent organizational audit, universal conformance certificate
  or a replacement for third-party review/replay. A finite corpus does not
  establish correctness for every hostile input.

## Parser and cryptographic sources

The MIT-licensed [Microsoft JSON parser](https://github.com/microsoft/node-jsonc-parser)
is pinned to `jsonc-parser@3.3.1`. Its parser can recover from errors, so this
wrapper requires an empty error list, disables comments/trailing commas/empty
content, checks duplicate names and bounds, and retains numeric token spelling
so `1.0`, `1e0` and `true` cannot become integer NumericDates. AST objects are
converted into null-prototype data objects; prototype-looking keys stay data.
The independently used [Ajv](https://ajv.js.org/json-schema.html) validator is pinned
to `ajv@8.20.0`. The lockfile records dependency integrity digests; no custom parser or
cryptographic primitive is introduced.

Node's [crypto verification API](https://nodejs.org/docs/latest-v22.x/api/crypto.html#cryptoverifyalgorithm-data-key-signature-callback)
uses an Ed25519 public key with a null algorithm argument as required by that
API. The wrapper separately requires the fully specified protected JOSE
identifier `Ed25519`. Both the existing production wrapper and Node may use
OpenSSL internally; this is independent profile logic, not a claim of unrelated
underlying cryptographic codebases.
