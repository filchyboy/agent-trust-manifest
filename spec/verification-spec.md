# Verification Extension Specification v0.1.0

## 1. Purpose

The verification extension records evidence that an ATM publisher's claims have been checked.

## 2. Verification levels

### `static`
Document and schema validation only.

### `active`
Live interaction checks against the running system.

### `audit`
Post-interaction inspection of logs, provenance records, or decision artifacts.

## 3. Verification record

A verification record includes:
- verifier identity
- method
- timestamp
- result
- optional report URI
- optional covered claims list

## 4. Result values

- `pass`
- `fail`
- `mixed`
- `unknown`

## 5. Consumer guidance

Consumers should prefer active or audit verification over static-only verification for higher-risk actions.
