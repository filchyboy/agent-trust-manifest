"""ATM detached JWS v1. Pure offline verification; no URL/key discovery here."""
import base64
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "consumer"))
from fetch_manifest import normalize_origin, FetchError

PROFILE = "atm-detached-jws/1"
MANIFEST = "application/atm-manifest+json"
FINDING = "application/atm-finding+json"
CRIT = ["b64", "atm_profile", "origin", "iat", "exp"]
LIMIT = 65536


class VerificationError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise VerificationError(reason)


def origin(value):
    try:
        require(normalize_origin(value) == value, "noncanonical_origin")
    except FetchError:
        raise VerificationError("invalid_origin") from None
    return value


def integer(value):
    return type(value) is int and 0 <= value <= 253402300799


def document(raw, limit=LIMIT):
    require(isinstance(raw, bytes) and len(raw) <= limit, "document_too_large")

    def pairs(items):
        obj = {}
        for key, value in items:
            require(key not in obj, "duplicate_member")
            obj[key] = value
        return obj

    def reject(value):
        raise VerificationError("invalid_json_number")

    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=reject)
        count = 0

        def bound(value, depth=0):
            nonlocal count
            count += 1
            require(depth <= 16 and count <= 2048, "overcomplex_json")
            if isinstance(value, str):
                require(len(value) <= 2048 and not any(0xD800 <= ord(c) <= 0xDFFF for c in value), "invalid_string")
            if isinstance(value, float):
                require(math.isfinite(value), "invalid_json_number")
            if isinstance(value, dict):
                for key, item in value.items():
                    require(len(key) <= 256, "overcomplex_json")
                    bound(key, depth + 1)
                    bound(item, depth + 1)
            if isinstance(value, list):
                require(len(value) <= 128, "overcomplex_json")
                for item in value:
                    bound(item, depth + 1)
        bound(obj)
        require(type(obj) is dict, "object_required")
        return obj
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, VerificationError):
            raise
        raise VerificationError("invalid_json") from None


def b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def unb64(value):
    require(isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]+", value)), "invalid_base64url")
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except ValueError:
        raise VerificationError("invalid_base64url") from None
    require(b64(raw) == value, "noncanonical_base64url")
    return raw


def header(raw, expected_origin, kind, now):
    h = document(raw, 2048)
    require(set(h) == {"alg", "kid", "typ", "b64", "crit", "atm_profile", "origin", "iat", "exp"}, "unsupported_header")
    require(h["alg"] == "Ed25519" and h["b64"] is False and h["crit"] == CRIT
            and h["atm_profile"] == PROFILE, "unsupported_profile")
    require(kind in (MANIFEST, FINDING) and h["typ"] == kind, "wrong_type")
    require(origin(h["origin"]) == origin(expected_origin), "wrong_origin")
    require(isinstance(h["kid"], str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", h["kid"])), "invalid_kid")
    require(integer(now) and integer(h["iat"]) and integer(h["exp"])
            and h["iat"] <= now < h["exp"] and h["iat"] < h["exp"]
            and h["exp"] - h["iat"] <= 86400, "invalid_signature_time")
    return h


def keyset(raw, expected_origin, now):
    obj = document(raw, 16384)
    require(set(obj) == {"profile", "origin", "issued_at", "expires_at", "keys"}
            and obj["profile"] == PROFILE, "invalid_jwks")
    require(origin(obj["origin"]) == origin(expected_origin), "wrong_key_origin")
    require(integer(obj["issued_at"]) and integer(obj["expires_at"])
            and obj["issued_at"] <= now < obj["expires_at"]
            and 0 < obj["expires_at"] - obj["issued_at"] <= 86400, "stale_or_invalid_jwks")
    require(type(obj["keys"]) is list and 1 <= len(obj["keys"]) <= 16, "invalid_keys")
    keys = {}
    for key in obj["keys"]:
        require(type(key) is dict and set(key) in (
            {"kty", "crv", "alg", "use", "kid", "x", "status", "nbf", "exp"},
            {"kty", "crv", "alg", "use", "kid", "x", "status", "nbf", "exp", "retired_at"}), "invalid_public_key")
        require(key["kty"] == "OKP" and key["crv"] == "Ed25519" and key["alg"] == "Ed25519"
                and key["use"] == "sig", "unsupported_key")
        kid = key["kid"]
        require(isinstance(kid, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", kid))
                and kid not in keys, "duplicate_or_invalid_kid")
        require(len(unb64(key["x"])) == 32, "invalid_key_length")
        require(key["status"] in ("active", "retired", "revoked", "compromised")
                and integer(key["nbf"]) and integer(key["exp"]) and key["nbf"] < key["exp"], "invalid_key_metadata")
        if key["status"] == "retired":
            require(integer(key.get("retired_at")) and key["nbf"] <= key["retired_at"] < key["exp"], "invalid_retirement")
        else:
            require("retired_at" not in key, "invalid_retirement")
        keys[kid] = key
    return keys


def verify(payload, signature, jwks, expected_origin, kind, now):
    document(payload)  # Reject ambiguous JSON even when correctly signed.
    require(isinstance(signature, bytes) and len(signature) <= 4096, "invalid_jws")
    try:
        protected, empty, encoded_sig = signature.decode("ascii").split(".")
    except (ValueError, UnicodeError):
        raise VerificationError("invalid_jws") from None
    require(empty == "", "payload_must_be_detached")
    h = header(unb64(protected), expected_origin, kind, now)
    keys = keyset(jwks, expected_origin, now)
    require(h["kid"] in keys, "unknown_key")
    key = keys[h["kid"]]
    require(key["status"] not in ("revoked", "compromised"), "revoked_key")
    require(key["nbf"] <= h["iat"] < key["exp"] and now < key["exp"], "key_time_invalid")
    if key["status"] == "retired":
        require(h["iat"] < key["retired_at"] <= now, "retired_key")
    sig = unb64(encoded_sig)
    require(len(sig) == 64, "invalid_signature_length")
    try:
        Ed25519PublicKey.from_public_bytes(unb64(key["x"])).verify(sig, protected.encode("ascii") + b"." + payload)
    except (InvalidSignature, ValueError):
        raise VerificationError("signature_mismatch") from None
    return h


def sign(payload, seed, issuer_origin, kind, kid, issued_at, expires_at):
    document(payload)
    require(isinstance(seed, bytes) and len(seed) == 32, "invalid_private_seed")
    h = {"alg": "Ed25519", "kid": kid, "typ": kind, "b64": False, "crit": CRIT,
         "atm_profile": PROFILE, "origin": issuer_origin, "iat": issued_at, "exp": expires_at}
    encoded = json.dumps(h, separators=(",", ":"), sort_keys=True).encode()
    header(encoded, issuer_origin, kind, issued_at)
    protected = b64(encoded)
    sig = Ed25519PrivateKey.from_private_bytes(seed).sign(protected.encode() + b"." + payload)
    return (protected + ".." + b64(sig)).encode("ascii")


def authenticate(payload, signature, jwks, expected_origin, kind, now):
    result = {"state": "unverified", "reason": "signature_not_supplied"}
    if signature is None:
        return result
    if jwks is None:
        return {"state": "unverified", "reason": "keys_not_supplied"}
    try:
        h = verify(payload, signature, jwks, expected_origin, kind, now)
        return {"state": "authenticated", "issuer": h["origin"], "kid": h["kid"],
                "expires_at": h["exp"], "reason": "signature_valid", "claims_truth": "unresolved"}
    except VerificationError as exc:
        return {"state": "invalid", "reason": str(exc)}


def applicable_manifest(manifest, expected_origin, now):
    # Structural validation remains local: never resolve evidence-provided schemas.
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    schemas = [json.loads(path.read_text()) for path in
               (Path(__file__).resolve().parents[2] / "schemas").glob("*.json")]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    schema = next(s for s in schemas if s["$id"].endswith("/agent-trust-manifest.schema.json"))
    require(Draft202012Validator(schema, registry=registry).is_valid(manifest), "invalid_manifest_schema")
    require(manifest["atm_version"] == "0.2.0" and manifest["issuer"]["uri"] == expected_origin
            and manifest["issuer"]["domain"].lower() == expected_origin.split("//", 1)[1].strip("[]"),
            "manifest_subject_mismatch")
    dates = []
    for field in ("published_at", "expires_at"):
        value = manifest[field]
        require(bool(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
                                 r"(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])", value))
                and not value.endswith("-00:00"), "invalid_manifest_time")
        try:
            dates.append(datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp())
        except (ValueError, OverflowError):
            raise VerificationError("invalid_manifest_time") from None
    require(dates[0] <= now < dates[1], "stale_or_future_manifest")


def inspect_finding(raw, signature, jwks, manifest_raw, platform_origin, assessor_origin, trusted_assessors, now):
    """Authenticate separately from applicability and explicit visitor acceptance."""
    result = {"authentication": authenticate(raw, signature, jwks, assessor_origin, FINDING, now),
              "applicability": "unresolved", "acceptance": "unresolved", "access_granted": False}
    try:
        require(isinstance(trusted_assessors, (list, tuple)) and len(trusted_assessors) <= 8, "too_many_assessors")
        selected = [origin(item) for item in trusted_assessors]
        require(result["authentication"]["state"] == "authenticated", "finding_not_authenticated")
        f = document(raw)
        require(set(f) == {"profile", "id", "assessor", "subject", "manifest_sha256", "claim", "observation", "issued_at", "expires_at", "method", "result", "limitations"}
                and f["profile"] == "atm-invocation-finding/1", "unsupported_finding")
        require(type(f["assessor"]) is dict and set(f["assessor"]) == {"origin", "relationship"}
                and f["assessor"]["origin"] == assessor_origin
                and f["assessor"]["relationship"] in ("independent", "affiliated", "self"), "assessor_mismatch")
        require(f["subject"] == {"origin": origin(platform_origin), "type": "platform"}, "wrong_subject")
        require(isinstance(f["id"], str) and bool(re.fullmatch(re.escape(assessor_origin) + r"/findings/[A-Za-z0-9_-]{1,64}", f["id"])), "invalid_finding_id")
        require(f["manifest_sha256"] == hashlib.sha256(manifest_raw).hexdigest(), "manifest_digest_mismatch")
        claim = f["claim"]
        require(type(claim) is dict and set(claim) == {"pointer", "value"}
                and claim["pointer"] == "/interaction_profile/explicit_invocation_required"
                and type(claim["value"]) is bool, "invalid_typed_claim")
        manifest = document(manifest_raw)
        applicable_manifest(manifest, platform_origin, now)
        value = manifest["interaction_profile"]["explicit_invocation_required"]
        require(type(value) is bool and value is claim["value"], "claim_value_mismatch")
        obs = f["observation"]
        require(type(obs) is dict and set(obs) == {"start", "end"}
                and all(integer(v) for v in (obs["start"], obs["end"], f["issued_at"], f["expires_at"]))
                and obs["start"] <= obs["end"] <= f["issued_at"] <= now < f["expires_at"]
                and f["expires_at"] - obs["start"] <= 86400, "invalid_finding_time")
        h = verify(raw, signature, jwks, assessor_origin, FINDING, now)
        require(h["iat"] == f["issued_at"] and h["exp"] == f["expires_at"], "finding_time_mismatch")
        require(f["method"] in ("static", "active", "audit") and f["result"] in ("pass", "fail", "unknown")
                and isinstance(f["limitations"], str) and bool(f["limitations"]), "invalid_finding_metadata")
        result.update(applicability="matched", declared_result=f["result"], method=f["method"],
                      relationship=f["assessor"]["relationship"], independence="unproven",
                      limitations=f["limitations"])
        require(assessor_origin in selected, "assessor_not_selected")
        require(assessor_origin != platform_origin and f["assessor"]["relationship"] == "independent", "independent_assessor_required")
        require(f["result"] == "pass" and claim["value"] is True, "finding_not_supportive")
        result.update(acceptance="accepted_for_claim", reason="visitor_selected_assessor")
    except VerificationError as exc:
        result["reason"] = str(exc)
    return result
