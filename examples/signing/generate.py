"""Reproduce fictional public test keys and immutable shared vectors. Never use in production."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/signing"))
import atm_signing as p

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
    write("vectors.json", {"warning": "PUBLIC FICTIONAL PRIVATE KEYS. NEVER USE THESE KEYS.", "vectors": vectors})


if __name__ == "__main__":
    main()
