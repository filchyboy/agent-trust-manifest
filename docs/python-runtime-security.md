# Python runtime security remediation

Date: 2026-11-07 America/Los_Angeles (2026-11-08 UTC).

## Finding and scope

The ATM development environment used Python 3.14.5 and pip 26.1.1. Its pip-vendored certifi 2026.02.25 retained emSign roots affected by the [eMudhra incident](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576). That is vulnerable software, not evidence that an installation was intercepted or the machine compromised. Passing functional tests does not establish runtime security.

Remediation is scoped to this ATM checkout. Global Homebrew Python installations, other projects' virtual environments and the global uv installation were not upgraded. The former ATM environment was retained separately as a rollback artifact, not as an approved runtime.

## Remediation

- Used the Python security team's SHA-256-pinned pip 26.2.2 wheel to bootstrap the old environment safely before additional package downloads.
- Installed a temporary uv 0.13.6 in that environment, then installed isolated native ARM64 Python runtimes through its official Python distribution catalog. No global Python executable links were changed.
- Selected Python 3.11.18 for the rebuilt ATM environment and CI configuration. This aligns with the existing CI minor series and avoids the Python 3.14.10 FIPS-mode regression described in [CVE-2026-119170](https://mail.python.org/archives/list/security-announce%40python.org/thread/PXVTTOBPUMFJSSUXN6XCS7FC5DZOSZXK/).
- Recreated the ATM environment with pip 26.2.2, whose vendored certifi is 2026.10.19, and installed the unchanged jsonschema 4.26.0 requirement through patched pip without cache reuse.
- Pinned the selected Python version in `.python-version` and CI, and added the advisory's hash-pinned pip bootstrap to CI and setup instructions.

The managed interpreter comes from Astral python-build-standalone build 20261026. uv verifies downloaded interpreter archives against the hashes in its release catalog. The native ARM64 3.11.18 archive's SHA-256 is `f3e1cd83a7f1d70e58b0d69102c18bd6867d2f973068dc5cbfd5822e445c66df`. [Catalog](https://github.com/astral-sh/uv/blob/0.13.6/crates/uv-python-managed/download-metadata.json)

The selected runtime reports OpenSSL 3.5.9. This record concerns the identified Python/pip issues; it is not a comprehensive audit of every dependency or other installation.

## CI observation and remaining verification

On the rebuilt Python 3.11.18 ARM64 environment, all 74 regression tests and all 21 workflow schema-validation commands passed. `pip check` and whitespace checks also passed. The newly installed Python 3.14.10 runtime is not selected by this checkout and was not used for these tests.

The latest existing [GitHub run](https://github.com/filchyboy/agent-trust-manifest/actions/runs/40244025139), from October 25, used Python 3.11.17. Its success does not verify the new patch or these local changes. The updated workflow has not been pushed or run on GitHub. Local macOS checks do not establish Linux runner equivalence.

The repository's dependency requirement remains jsonschema 4.26.0. Runtime security maintenance is separate from ATM schema compatibility and trust semantics.
