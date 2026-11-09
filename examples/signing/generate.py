"""Reproduce fictional public test keys and immutable shared vectors. Never use in production."""
import hashlib
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.signing import atm_signing as p

HERE = Path(__file__).resolve().parent
START, NOW, END = 1791306000, 1791309600, 1791313200  # 2026-10-06 17/18/19 UTC
PUBLISHER = "https://consumer-demo.example"
ASSESSOR = "https://assessor.example"


def write(name, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    (HERE / name).write_bytes(raw)
    return raw


def keys(issuer, seed):
    return {"profile": p.PROFILE, "origin": issuer, "issued_at": START, "expires_at": END,
            "keys": [{"kty": "OKP", "crv": "Ed25519", "alg": "Ed25519", "use": "sig", "kid": "fictional-1",
                      "x": p.b64(p.Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes_raw()),
                      "status": "active", "nbf": START, "exp": END}]}


def negative_cases(vectors):
    """Export exact hostile inputs, not Python mutation recipes, for any implementation."""
    cases = []
    base = vectors[0]
    payload = (HERE / base["payload"]).read_bytes()
    signature = (HERE / base["signature"]).read_bytes()
    jwks = json.loads((HERE / base["jwks"]).read_bytes())
    protected, _, sig = signature.split(b".")

    def add(identifier, reason, base_vector=base["payload"], independent_crypto=False, **overrides):
        cases.append({"id": identifier, "base_vector": base_vector, "overrides": overrides,
                      "expected_reason": reason, "independent_crypto": independent_crypto})

    def changed_header(field, value):
        h = copy.deepcopy(base["protected_header"])
        h[field] = value
        return p.b64(json.dumps(h, separators=(",", ":")).encode()).encode() + b".." + sig

    def changed_keys(field, value):
        k = copy.deepcopy(jwks)
        k["keys"][0][field] = value
        return json.dumps(k, separators=(",", ":")).encode().hex()

    add("payload-whitespace-tamper", "signature_mismatch", independent_crypto=True, payload_hex=(payload + b" ").hex())
    bad_sig = bytearray(p.unb64(sig.decode())); bad_sig[0] ^= 1
    add("signature-bit-tamper", "signature_mismatch", independent_crypto=True,
        signature_hex=(protected + b".." + p.b64(bytes(bad_sig)).encode()).hex())
    other_x = json.loads((HERE / "assessor.jwks.json").read_bytes())["keys"][0]["x"]
    add("wrong-public-key-same-origin-kid", "signature_mismatch", independent_crypto=True, jwks_hex=changed_keys("x", other_x))
    finding = (HERE / "finding.json").read_bytes()
    add("finding-bytes-tamper", "signature_mismatch", base_vector="finding.json", independent_crypto=True,
        payload_hex=(finding + b" ").hex())
    for identifier, field, value, reason in [
        ("alg-none", "alg", "none", "unsupported_profile"),
        ("alg-polymorphic-eddsa", "alg", "EdDSA", "unsupported_profile"),
        ("encoded-payload-not-allowed", "b64", True, "unsupported_profile"),
        ("unknown-critical-parameter", "crit", ["b64", "unknown"], "unsupported_profile"),
        ("untrusted-key-url", "jku", "https://evil.example/key", "unsupported_header"),
        ("unknown-kid", "kid", "unknown", "unknown_key"),
        ("expired-signature", "exp", NOW, "invalid_signature_time"),
        ("future-signature", "iat", NOW + 1, "invalid_signature_time"),
        ("fractional-iat", "iat", float(START), "invalid_signature_time"),
        ("boolean-exp", "exp", True, "invalid_signature_time"),
        ("overlong-signature-window", "exp", START + 86401, "invalid_signature_time"),
        ("noncanonical-protected-origin", "origin", PUBLISHER + "/", "noncanonical_origin"),
    ]:
        add(identifier, reason, signature_hex=changed_header(field, value).hex())
    add("wrong-expected-origin", "wrong_origin", origin=ASSESSOR)
    add("wrong-expected-type", "wrong_type", type=p.FINDING)
    for status in ("revoked", "compromised"):
        add(status + "-backdated-key", "revoked_key", jwks_hex=changed_keys("status", status))
    for identifier, field, value, reason in [
        ("private-key-material", "d", "never-publish-secrets", "invalid_public_key"),
        ("wrong-public-key-length", "x", p.b64(b"x" * 31), "invalid_key_length"),
        ("expired-key", "exp", NOW, "key_time_invalid"),
        ("future-key", "nbf", NOW, "key_time_invalid"),
    ]:
        add(identifier, reason, jwks_hex=changed_keys(field, value))
    for identifier, field, value, reason in [
        ("stale-key-snapshot", "expires_at", NOW, "stale_or_invalid_jwks"),
        ("future-key-snapshot", "issued_at", NOW + 1, "stale_or_invalid_jwks"),
        ("overlong-key-snapshot-window", "expires_at", START + 86401, "stale_or_invalid_jwks"),
        ("wrong-key-origin", "origin", ASSESSOR, "wrong_key_origin"),
        ("duplicate-kid", "keys", jwks["keys"] * 2, "duplicate_or_invalid_kid"),
    ]:
        k = copy.deepcopy(jwks); k[field] = value
        add(identifier, reason, jwks_hex=json.dumps(k, separators=(",", ":")).encode().hex())
    retired = copy.deepcopy(jwks); retired["keys"][0].update(status="retired", retired_at=START)
    add("signature-at-retirement-cutoff", "retired_key", jwks_hex=json.dumps(retired).encode().hex())
    add("base64-padding", "invalid_base64url", signature_hex=(protected + b".." + sig + b"=").hex())
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    last = alphabet[alphabet.index(chr(sig[-1])) + 1].encode()
    add("nonzero-base64-pad-bits", "noncanonical_base64url", signature_hex=(protected + b".." + sig[:-1] + last).hex())
    add("attached-payload", "payload_must_be_detached", signature_hex=(protected + b".payload." + sig).hex())
    duplicate = p.unb64(protected.decode())[:-1] + b',"alg":"Ed25519"}'
    add("duplicate-protected-member", "duplicate_member", signature_hex=(p.b64(duplicate).encode() + b".." + sig).hex())
    for identifier, body, reason in [
        ("duplicate-payload-member", b'{"x":1,"x":2}', "duplicate_member"),
        ("nonfinite-payload", b'{"x":NaN}', "invalid_json_number"),
        ("invalid-utf8-payload", b'{"x":"' + bytes([255]) + b'"}', "invalid_json"),
    ]:
        add(identifier, reason, payload_hex=body.hex())
    add("invalid-protected-json", "invalid_json", signature_hex=(p.b64(b"{").encode() + b".." + sig).hex())
    add("short-signature", "invalid_signature_length", signature_hex=(protected + b"..AA").hex())
    return cases


def main():
    publisher_seed, assessor_seed = bytes(range(32)), bytes(range(32, 64))
    manifest = json.loads((HERE.parent / "consumer/manifest.json").read_bytes())
    manifest["verification"] = {"level": "active", "verified_by": [{"entity": "Fictional Assessor", "method": "active",
        "timestamp": "2026-10-06T17:55:00Z", "result": "pass",
        "report_uri": ASSESSOR + "/findings/invocation-1"}]}
    raw = write("manifest.json", manifest)
    write("publisher.jwks.json", keys(PUBLISHER, publisher_seed))
    write("assessor.jwks.json", keys(ASSESSOR, assessor_seed))
    finding = write("finding.json", {"profile": "atm-invocation-finding/1",
        "id": ASSESSOR + "/findings/invocation-1", "assessor": {"origin": ASSESSOR, "relationship": "independent"},
        "subject": {"origin": PUBLISHER, "type": "platform"}, "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "claim": {"pointer": "/interaction_profile/explicit_invocation_required", "value": True},
        "observation": {"start": START, "end": START + 3300}, "issued_at": START + 3300, "expires_at": END,
        "method": "active", "result": "pass",
        "limitations": "Fictional observation of one platform claim; no live tests, deployment binding, or independence investigation occurred."})
    vectors = []
    for name, payload, seed, issuer, kind, iat, jwks in [
        ("manifest", raw, publisher_seed, PUBLISHER, p.MANIFEST, START, "publisher.jwks.json"),
        ("finding", finding, assessor_seed, ASSESSOR, p.FINDING, START + 3300, "assessor.jwks.json"),
    ]:
        signature = p.sign(payload, seed, issuer, kind, "fictional-1", iat, END)
        (HERE / (name + ".jws")).write_bytes(signature)
        protected = signature.split(b".")[0]
        vectors.append({"payload": name + ".json", "signature": name + ".jws", "jwks": jwks,
                        "origin": issuer, "type": kind, "now": NOW,
                        "fictional_private_seed_hex": seed.hex(),
                        "protected_header": p.document(p.unb64(protected.decode())),
                        "signing_input_hex": (protected + b"." + payload).hex(),
                        "payload_sha256": hashlib.sha256(payload).hexdigest(),
                        "signature_hex": p.unb64(signature.split(b".")[2].decode()).hex()})
    write("vectors.json", {"warning": "PUBLIC FICTIONAL PRIVATE KEYS. NEVER USE THESE KEYS.", "vectors": vectors,
                           "negative_vectors": negative_cases(vectors)})


if __name__ == "__main__":
    main()
