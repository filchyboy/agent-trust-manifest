"""Inspect declarations and explicitly supplied evidence; never grant access."""
import argparse
import hashlib
import hmac
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fetch_manifest import FetchError, MAX_BYTES, normalize_origin

ROOT = Path(__file__).resolve().parents[2]
FETCH_TIMEOUT = 8
STATUS_PATH = "/.well-known/operational-status.json"
STATUS_SCHEMA = "https://agenttrustmanifest.org/schemas/operational-status-feed.schema.json"
CLAIMS = ("content_triggered_execution", "explicit_invocation_required",
          "provenance_available", "audit_logging_available")
_validators = None


class ConsumerError(Exception):
    pass


def decode_document(raw):
    if len(raw) > MAX_BYTES:
        raise ConsumerError("document_too_large")

    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError()
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError()

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs,
                           parse_constant=reject_constant)
        if not isinstance(value, dict):
            raise ValueError()
        count = 0

        def bounded(item, depth=0):
            nonlocal count
            count += 1
            if depth > 16 or count > 2048:
                raise ValueError()
            if isinstance(item, str) and len(item) > 2048:
                raise ValueError()
            if isinstance(item, float) and not math.isfinite(item):
                raise ValueError()
            if isinstance(item, dict):
                for key, sub in item.items():
                    if len(key) > 256:
                        raise ValueError()
                    bounded(sub, depth + 1)
            elif isinstance(item, list):
                if len(item) > 128:
                    raise ValueError()
                for sub in item:
                    bounded(sub, depth + 1)

        bounded(value)
        return value
    except (UnicodeError, ValueError, RecursionError):
        raise ConsumerError("invalid_or_overcomplex_json") from None


def read_file(path):
    try:
        if not Path(path).is_file():
            raise OSError()
        with Path(path).open("rb") as stream:
            value = stream.read(MAX_BYTES + 1)
    except OSError:
        raise ConsumerError("file_unavailable") from None
    if len(value) > MAX_BYTES:
        raise ConsumerError("document_too_large")
    return value


def validate(value, schema_name):
    global _validators
    if _validators is None:
        try:
            from jsonschema import Draft202012Validator
            from referencing import Registry, Resource
        except ImportError:
            raise ConsumerError("jsonschema_dependency_missing") from None
        schemas = {p.name: json.loads(p.read_text()) for p in (ROOT / "schemas").glob("*.json")}
        # No schema or $ref supplied by a remote document is ever loaded.
        registry = Registry().with_resources(
            (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
        )
        _validators = {name: Draft202012Validator(schema, registry=registry)
                       for name, schema in schemas.items()}
    return _validators[schema_name].is_valid(value)


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
            r"(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])", value):
        raise ConsumerError("invalid_timestamp")
    if value.endswith("-00:00"):
        raise ConsumerError("invalid_timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        raise ConsumerError("invalid_timestamp") from None


def freshness(value, now):
    if "published_at" not in value or "expires_at" not in value:
        return "missing"
    try:
        published, expires = timestamp(value["published_at"]), timestamp(value["expires_at"])
    except ConsumerError:
        return "invalid"
    if expires <= published or published > now:
        return "invalid"
    return "stale" if now >= expires else "fresh"


def same_subject(value, origin):
    return (value.get("issuer", {}).get("id") == origin
            and value.get("subject") == {"id": origin, "type": "platform"}
            and value.get("scope") == {"level": "platform", "identifier": origin})


def inspect_evidence(manifest, raw, origin, now):
    evidence = {"state": "missing", "authentication": "unverified",
                "prerequisites_met": False, "cache_ttl_enforced": False,
                "reason": "status_reference_missing"}
    refs = [x for x in manifest.get("governance_artifacts", [])
            if x["type"] == "operational_status_feed"]
    if not refs:
        return evidence
    if len(refs) != 1:
        evidence.update(state="invalid", reason="ambiguous_status_references")
        return evidence
    ref = refs[0]
    if (ref["uri"] != origin + STATUS_PATH or ref["schema_uri"] != STATUS_SCHEMA
            or ref["version"] != "0.2.0" or not same_subject(ref, origin)):
        evidence.update(state="invalid", reason="unsupported_reference_or_scope")
        return evidence
    evidence["declared_revocation_status"] = ref.get("revocation_status", "missing")
    evidence["revocation_checked"] = False
    if ref.get("revocation_status") != "active":
        evidence.update(state="unverified", reason="declared_revocation_not_active")
        return evidence
    state = freshness(ref, now)
    evidence["reference_freshness"] = state
    if state != "fresh":
        evidence.update(state=state, reason="reference_freshness_" + state)
        return evidence
    if raw is None:
        evidence["reason"] = "status_file_not_supplied"
        return evidence
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", ref["hash"]):
        evidence.update(state="invalid", reason="declared_digest_invalid")
        return evidence
    if not hmac.compare_digest(ref["hash"][7:], hashlib.sha256(raw).hexdigest()):
        evidence.update(state="invalid", digest="mismatch", reason="status_digest_mismatch")
        return evidence
    evidence["digest"] = "matched"
    try:
        status = decode_document(raw)
    except ConsumerError as exc:
        evidence.update(state="invalid", reason=str(exc))
        return evidence
    if not validate(status, "operational-status-feed.schema.json"):
        evidence.update(state="invalid", schema="invalid", reason="status_schema_invalid")
        return evidence
    evidence["schema"] = "valid"
    if status["feed_version"] != "0.2.0":
        evidence.update(state="invalid", reason="unsupported_status_version")
        return evidence
    state = freshness(status, now)
    evidence["status_freshness"] = state
    if state != "fresh":
        evidence.update(state=state, reason="status_freshness_" + state)
        return evidence
    if not same_subject(status, origin):
        evidence.update(state="invalid", reason="unsupported_status_scope")
        return evidence
    evidence["scope"] = "claimed_match"
    evidence["reported_status"] = status["overall_status"]
    if status["overall_status"] != "operational":
        evidence.update(state="unverified", reason="reported_status_not_operational")
        return evidence
    evidence.update(state="unverified", prerequisites_met=True,
                    reason="hash_match_is_not_authentication")
    return evidence


def platform_controls_report(reason="platform_profile_missing"):
    return {"state": "unresolved", "authentication": "unverified",
            "declaration_checks_passed": False, "capability_existence": "unresolved",
            "caller_eligibility": "unresolved", "approval_granted": False,
            "reason": reason}


def base_report():
    return {"profile": "atm-consumer-demo/0.2", "manifest": {"state": "invalid"},
            "declared_claims": {}, "available_evidence": [],
            "status_evidence": {"state": "missing", "authentication": "unverified"},
            "platform_controls": platform_controls_report("profile_not_supplied"),
            "policy": {"decision": "hold", "access_granted": False,
                       "caller_eligibility": "unresolved", "approval_granted": False,
                       "runtime_enforcement_performed": False, "reasons": []}}


def inspect(manifest_raw, status_raw, origin, now, profile_raw=None, expected_context=None):
    report = base_report()
    try:
        manifest = decode_document(manifest_raw)
    except ConsumerError as exc:
        report["policy"]["reasons"] = [str(exc)]
        return report
    if not validate(manifest, "agent-trust-manifest.schema.json"):
        report["manifest"]["schema"] = "invalid"
        report["policy"]["reasons"] = ["manifest_schema_invalid"]
        return report
    report["manifest"].update(schema="valid", authentication="unverified",
                              origin_binding="unverified")
    if len(manifest.get("governance_artifacts", [])) > 32:
        report["policy"]["reasons"] = ["too_many_artifact_references"]
        return report
    report["declared_claims"] = {key: manifest["interaction_profile"][key] for key in CLAIMS}
    report["available_evidence"] = [{"type": x["type"], "state": "unverified",
                                     "automatically_fetched": False}
                                    for x in manifest.get("governance_artifacts", [])]
    for field in ("verification", "reputation", "attestation"):
        if field in manifest:
            report["available_evidence"].append({"type": field, "state": "unverified",
                                                 "automatically_fetched": False})
    if manifest["atm_version"] != "0.2.0":
        report["policy"]["reasons"] = ["unsupported_atm_version"]
        return report
    state = freshness(manifest, now)
    report["manifest"]["state"] = state
    if state != "fresh":
        report["policy"]["reasons"] = ["manifest_freshness_" + state]
        return report
    try:
        origin_matches = (normalize_origin(manifest["issuer"]["uri"]) == origin
                          and manifest["issuer"]["domain"].lower()
                          == urlsplit(origin).hostname)
    except FetchError:
        origin_matches = False
    if not origin_matches:
        report["policy"]["reasons"] = ["issuer_origin_mismatch"]
        return report
    report["manifest"]["origin_binding"] = "claimed_match"
    evidence = inspect_evidence(manifest, status_raw, origin, now)
    report["status_evidence"] = evidence
    reasons = []
    if report["declared_claims"]["explicit_invocation_required"] is not True:
        reasons.append("explicit_invocation_not_declared")
    if report["declared_claims"]["content_triggered_execution"] is not False:
        reasons.append("content_execution_not_excluded")
    if not evidence["prerequisites_met"]:
        reasons.append(evidence["reason"])
    if reasons:
        report["policy"]["reasons"] = reasons
    else:
        report["policy"].update(decision="manual_review", reasons=[
            "issuer_authentication_unverified", "claims_not_independently_verified",
            "revocation_not_checked",
        ])
    if profile_raw is not None or expected_context is not None:
        controls = inspect_platform_controls(profile_raw, expected_context, manifest, origin, now)
        report["platform_controls"] = controls
        if not controls["declaration_checks_passed"]:
            report["policy"].update(decision="hold")
        report["policy"]["reasons"].append(controls["reason"])
    return report


def inspect_platform_controls(raw, expected, manifest, origin, now):
    """Compare declarations with a separately supplied context; authenticate nothing."""
    result = platform_controls_report()

    def unresolved(reason):
        result["reason"] = reason
        return result

    if raw is None:
        return result
    if expected is None or not validate(expected, "platform-context-draft-0.1.schema.json"):
        return unresolved("expected_context_missing_or_invalid")
    refs = [ref for ref in manifest.get("governance_artifacts", [])
            if ref["type"] == "platform_policy"]
    if len(refs) != 1:
        return unresolved("platform_profile_reference_missing_or_ambiguous")
    ref = refs[0]
    if (ref["schema_uri"] != "https://agenttrustmanifest.org/schemas/platform-controls-draft-0.1.schema.json"
            or ref["version"] != "platform-controls-draft/0.1"
            or ref["uri"] != origin + "/.well-known/platform-controls.json"
            or ref["issuer"] != {"id": manifest["issuer"]["uri"]}
            or ref["subject"] != expected["subject"]
            or ref["scope"] != {"level": "surface", "identifier": expected["scope"]["surface"]}):
        return unresolved("platform_profile_reference_mismatch")
    state = freshness(ref, now)
    if state != "fresh":
        return unresolved("profile_reference_freshness_" + state)
    if ref.get("revocation_status") != "active":
        return unresolved("profile_reference_revocation_unresolved")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", ref["hash"]):
        return unresolved("profile_digest_invalid")
    if not hmac.compare_digest(ref["hash"][7:], hashlib.sha256(raw).hexdigest()):
        return unresolved("profile_digest_mismatch")
    try:
        profile = decode_document(raw)
    except ConsumerError as exc:
        return unresolved("profile_" + str(exc))
    if not validate(profile, "platform-controls-draft-0.1.schema.json"):
        return unresolved("platform_profile_schema_invalid")
    if (profile["atm_version"] != manifest["atm_version"]
            or profile["manifest_version"] != manifest["manifest_version"]
            or profile["publisher"]["id"] != manifest["issuer"]["uri"]
            or profile["origin"] != origin):
        return unresolved("profile_manifest_binding_mismatch")
    if profile["subject"] != expected["subject"]:
        return unresolved("profile_subject_mismatch")
    for key in ("deployment", "tenant", "surface", "policy_version"):
        if profile["scope"][key] != expected["scope"][key]:
            return unresolved("profile_" + key + "_mismatch")
    state = freshness(profile, now)
    if state != "fresh":
        return unresolved("profile_freshness_" + state)
    capabilities = [c for c in profile["capabilities"] if c["id"] == expected["capability_id"]]
    if len(capabilities) != 1:
        return unresolved("capability_unresolved")
    cap = capabilities[0]
    result.update(capability_existence="declared", capability={
        "id": cap["id"], "platform_permission": cap["platform_permission"],
        "access_conditions": cap["access_conditions"], "approval_required": cap["approval_required"]})
    # The declarations are observable, but no condition is fulfilled by discovery.
    if cap["platform_permission"] == "refused":
        return unresolved("platform_refusal_declared")
    if cap["platform_permission"] != "allowed":
        return unresolved("platform_permission_unresolved")
    if len(profile["evidence"]) != 1:
        return unresolved("evidence_missing_or_ambiguous")
    evidence = profile["evidence"][0]
    applies = evidence["applies_to"]
    if applies["subject"] != expected["subject"]:
        return unresolved("evidence_subject_mismatch")
    for key in ("deployment", "tenant", "surface", "policy_version"):
        if applies["scope"][key] != expected["scope"][key]:
            return unresolved("evidence_" + key + "_mismatch")
    if applies["capability_id"] != expected["capability_id"]:
        return unresolved("evidence_capability_mismatch")
    assessed_controls = {"control_authority": profile["control_authority"],
                         "enforcement_point": profile["enforcement_point"], "capability": cap}
    if evidence["assessed_controls"] != assessed_controls:
        return unresolved("evidence_controls_mismatch")
    state = freshness({"published_at": evidence["observed_at"],
                       "expires_at": evidence["expires_at"]}, now)
    if state != "fresh":
        return unresolved("evidence_freshness_" + state)
    if evidence["result"] != "pass":
        return unresolved("assessment_not_pass")
    result.update(state="unverified", declaration_checks_passed=True,
                  reason="platform_controls_not_authenticated")
    return result


def fetch_manifest(origin):
    origin = normalize_origin(origin)
    try:
        run = subprocess.run([sys.executable, "-B", str(Path(__file__).with_name("fetch_manifest.py")),
                              origin], capture_output=True, timeout=FETCH_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise ConsumerError("fetch_timeout") from None
    except OSError:
        raise ConsumerError("fetch_failed") from None
    if run.returncode:
        allowed = {"invalid_origin", "unsafe_address", "redirect_rejected", "http_failure",
                   "unsupported_content_type", "unsupported_encoding", "ambiguous_length",
                   "document_too_large", "network_failure"}
        code = run.stderr.decode("ascii", errors="ignore").strip()
        raise ConsumerError(code if code in allowed else "fetch_failed")
    if len(run.stdout) > MAX_BYTES:
        raise ConsumerError("document_too_large")
    return run.stdout


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", help="Explicit local manifest file (offline)")
    source.add_argument("--origin", help="Public HTTPS origin; fetch only its well-known manifest")
    parser.add_argument("--expected-origin", help="Required claimed-origin expectation in offline mode")
    parser.add_argument("--status-file", help="Explicit local operational status bytes; never auto-fetched")
    parser.add_argument("--at", help="Fixture-only RFC3339 decision time; prohibited for network mode")
    parser.add_argument("--platform-profile-file", help="Explicit draft platform-control sidecar; never fetched")
    parser.add_argument("--expected-context-file", help="Separately selected platform/deployment/scope/capability/policy context")
    args = parser.parse_args(argv)
    report = base_report()
    try:
        if args.manifest:
            if not args.expected_origin:
                raise ConsumerError("expected_origin_required")
            origin = normalize_origin(args.expected_origin)
            raw = read_file(args.manifest)
        else:
            if args.at or args.expected_origin:
                raise ConsumerError("offline_option_in_network_mode")
            origin = normalize_origin(args.origin)
            raw = fetch_manifest(origin)
        status_error = None
        try:
            status = read_file(args.status_file) if args.status_file else None
        except ConsumerError as exc:
            status, status_error = None, str(exc)
        now = timestamp(args.at) if args.at else datetime.now(timezone.utc)
        profile_raw, expected_context, profile_input_error = None, None, None
        if args.platform_profile_file or args.expected_context_file:
            if not (args.platform_profile_file and args.expected_context_file):
                profile_input_error = "profile_and_expected_context_required"
            else:
                source = "platform_profile"
                try:
                    profile_raw = read_file(args.platform_profile_file)
                    source = "expected_context"
                    expected_context = decode_document(read_file(args.expected_context_file))
                except ConsumerError as exc:
                    profile_raw, expected_context = None, None
                    profile_input_error = source + "_" + str(exc)
        report = inspect(raw, status, origin, now, profile_raw, expected_context)
        if profile_input_error:
            report["platform_controls"] = platform_controls_report(profile_input_error)
            report["policy"]["decision"] = "hold"
            report["policy"]["reasons"].append(profile_input_error)
        if status_error:
            report["status_evidence"].update(
                state="missing" if status_error == "file_unavailable" else "invalid",
                reason="status_" + status_error, prerequisites_met=False)
            reasons = [x for x in report["policy"]["reasons"] if x != "status_file_not_supplied"]
            report["policy"].update(decision="hold", reasons=reasons + ["status_" + status_error])
    except (ConsumerError, FetchError) as exc:
        report["policy"]["reasons"] = [str(exc)]
        if str(exc) in {"file_unavailable", "network_failure", "fetch_timeout", "fetch_failed", "http_failure"}:
            report["manifest"]["state"] = "missing"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["policy"]["decision"] == "manual_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
