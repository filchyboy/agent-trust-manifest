# Unreleased validator hardening

The optional CLI now uses a local `referencing.Registry` rather than deprecated `RefResolver`. Its default retains structural validation without format enforcement. An explicit `--strict-formats` mode checks formats using pinned URI and RFC3339 dependencies. Existing valid examples retain their meaning; no JSON Schema assertions, required fields, enums or core version contracts change.

The CLI supports the repository's Draft 2020-12 schemas. References resolve only from neighboring `*.schema.json` files; unknown references fail, with no network retrieval. Duplicate object keys and nonfinite JSON constants are rejected rather than silently normalized. Errors are sorted by JSON pointer then message; root errors use `<root>`. Exit codes: 0 checked constraints passed, 1 document validation failed, 2 input/schema/dependency/reference error. Scripts should use exit codes rather than depend on the previous `VALID:` display prefix.

Strict formats are not full ATM conformance, authentication, current freshness, signature verification, hash comparison, safe URL retrieval or truth checking. In particular, legacy schema permissions for arbitrary version/algorithm strings, empty signatures/hashes and empty verification arrays remain. Tightening these contracts requires an explicit compatibility decision, not a hidden CLI change. The consumer's bounded semantic rules remain separate.

Regression tests cover both modes, URI/date-time failures, invalid dates, missing fields, wrong types, malformed JSON, duplicate keys, nonfinite constants, invalid UTF-8, missing files, bad schemas and unresolved references. They also explicitly preserve the boundary that format-valid documents can contain unauthenticated or insufficient declarations.
