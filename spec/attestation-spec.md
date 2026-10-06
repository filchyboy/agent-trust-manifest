# Attestation Extension Specification v0.1.0

## 1. Purpose

The attestation extension binds manifest claims to identity and, optionally, to deployment state.

## 2. Assurance levels

### `signed_manifest`
The manifest is digitally signed by the publisher.

### `deployment_bound`
The manifest is signed and bound to deployment identifiers such as a build SHA or policy bundle hash.

### `hardware_attested`
The manifest is bound to an attested runtime or trusted execution environment.

## 3. Required fields

- `type`
- `alg`
- `key_id`
- `issued_at`
- `expires_at`
- `signature`

## 4. Optional deployment binding

- `build_sha`
- `policy_bundle_sha`
- `runtime_profile`
- `container_image_digest`

## 5. Consumer guidance

Consumers should reject expired attestations and should verify signatures before relying on claims.

## 6. Implementation status

This draft describes attestation fields and consumer responsibilities. The repository does not implement signing or signature-verification helpers. Its example signatures and deployment identifiers are fictional placeholders, not cryptographic evidence.
