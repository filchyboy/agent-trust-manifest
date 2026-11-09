# Development setup and runtime security

Use an isolated project environment; these commands do not upgrade global
Homebrew/Python installations or other projects. CI and `.python-version`
currently select Python 3.11.18. Check the actual interpreter version, and
review pins when applying future security updates.

## Python setup

The project retains the Python security advisory's hash-pinned pip bootstrap.
A patched interpreter does not update an older virtual environment's pip.
Bootstrap before downloading project dependencies:

```sh
python3.11 --version
python3.11 -m venv .venv
.venv/bin/python -m pip --isolated --disable-pip-version-check install --no-cache-dir --no-deps 'pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70'
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

If that exact interpreter is unavailable, install a patched isolated runtime
through your environment's supported process. Do not downgrade a global
runtime or silently substitute an unverified patch version.

## Tests and independent verifier

The Python suite also uses Node for the existing vector harness. CI selects
Node 22. For the separate local verifier prototype, install its locked parser
with package scripts disabled; it does not modify global npm settings:

```sh
.venv/bin/python -m unittest discover -s tests
.venv/bin/python tools/signing/check_vectors.py
node tools/signing/interop.mjs
npm ci --ignore-scripts --prefix tools/independent-verifier
npm test --prefix tools/independent-verifier
git diff --check
```

The workflow lists the fixture-to-schema validation commands. Its explicit
`--strict-formats` checks supplement the validator's structural default;
passing either mode is not cryptographic or substantive claim validation.
Read the independent verifier's scope before treating its results as evidence
of broader protocol conformance.

## Historical remediation record

The content below records the November 7 remediation snapshot. Its runtime
versions, test counts and then-unpushed CI state are historical observations,
not claims about today's machine or latest remote run. Useful security context
is preserved here rather than mixed with current quick-start instructions.

### Python runtime security remediation

Date: 2026-11-07 America/Los_Angeles (2026-11-08 UTC).

#### Finding and scope

The ATM development environment used Python 3.14.5 and pip 26.1.1. Its pip-vendored certifi 2026.02.25 retained emSign roots affected by the [eMudhra incident](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576). That is vulnerable software, not evidence that an installation was intercepted or the machine compromised. Passing functional tests does not establish runtime security.

Remediation is scoped to this ATM checkout. Global Homebrew Python installations, other projects' virtual environments and the global uv installation were not upgraded. The former ATM environment was retained separately as a rollback artifact, not as an approved runtime.

#### Remediation

- Used the Python security team's SHA-256-pinned pip 26.2.2 wheel to bootstrap the old environment safely before additional package downloads.
- Installed a temporary uv 0.13.6 in that environment, then installed isolated native ARM64 Python runtimes through its official Python distribution catalog. No global Python executable links were changed.
- Selected Python 3.11.18 for the rebuilt ATM environment and CI configuration. This aligns with the existing CI minor series and avoids the Python 3.14.10 FIPS-mode regression described in [CVE-2026-119170](https://mail.python.org/archives/list/security-announce%40python.org/thread/PXVTTOBPUMFJSSUXN6XCS7FC5DZOSZXK/).
- Recreated the ATM environment with pip 26.2.2, whose vendored certifi is 2026.10.19, and installed the unchanged jsonschema 4.26.0 requirement through patched pip without cache reuse.
- Pinned the selected Python version in `.python-version` and CI, and added the advisory's hash-pinned pip bootstrap to CI and setup instructions.

The managed interpreter comes from Astral python-build-standalone build 20261026. uv verifies downloaded interpreter archives against the hashes in its release catalog. The native ARM64 3.11.18 archive's SHA-256 is `f3e1cd83a7f1d70e58b0d69102c18bd6867d2f973068dc5cbfd5822e445c66df`. [Catalog](https://github.com/astral-sh/uv/blob/0.13.6/crates/uv-python-managed/download-metadata.json)

The selected runtime reports OpenSSL 3.5.9. This record concerns the identified Python/pip issues; it is not a comprehensive audit of every dependency or other installation.

#### CI observation and remaining verification

On the rebuilt Python 3.11.18 ARM64 environment, all 74 regression tests and all 21 workflow schema-validation commands passed. `pip check` and whitespace checks also passed. The newly installed Python 3.14.10 runtime is not selected by this checkout and was not used for these tests.

The latest existing [GitHub run](https://github.com/filchyboy/agent-trust-manifest/actions/runs/40244025139), from October 25, used Python 3.11.17. Its success does not verify the new patch or these local changes. The updated workflow has not been pushed or run on GitHub. Local macOS checks do not establish Linux runner equivalence.

The repository's dependency requirement remains jsonschema 4.26.0. Runtime security maintenance is separate from ATM schema compatibility and trust semantics.
