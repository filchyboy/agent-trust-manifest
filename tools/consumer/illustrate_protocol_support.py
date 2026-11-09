"""Non-normative offline reading of ATM mechanism declarations; no protocol adapters."""
import argparse
import json
from datetime import datetime, timezone

from consume import ConsumerError, decode_document, freshness, read_file, timestamp, validate

IDENTITY_FIELDS = ("protocol_id", "specification_uri", "version", "profile")


def identity(mechanism):
    return tuple(mechanism[field] for field in IDENTITY_FIELDS)


def illustrate(raw, expected_raw, vocabulary_raw, now):
    """Illustrative triage choices, not ATM schema requirements or authorization."""
    report = {"illustration": "protocol-support-reader/0.1", "state": "unresolved",
              "authentication": "unverified", "scope_match": "unresolved",
              "mechanisms": {}, "requirements": [], "requirements_satisfied": False,
              "access_granted": False, "approval_granted": False,
              "caller_eligibility": "unresolved", "interoperability_verified": False,
              "runtime_enforcement_performed": False,
              "manifest_binding_checked": False, "reason": "input_unresolved"}
    try:
        document = decode_document(raw)
        expected = decode_document(expected_raw)
        vocabulary = decode_document(vocabulary_raw)
    except ConsumerError as exc:
        report["reason"] = str(exc)
        return report
    # decode_document deliberately accepts only objects. The vocabulary wrapper
    # is separate input, never inferred from declarations as evidence of support.
    if not validate(document, "protocol-support-draft-0.1.schema.json"):
        report["reason"] = "declaration_schema_invalid"
        return report
    if not validate(expected, "platform-context-draft-0.1.schema.json"):
        report["reason"] = "expected_context_invalid"
        return report
    if not validate(vocabulary, "protocol-vocabulary-demo-0.1.schema.json"):
        report["reason"] = "vocabulary_invalid"
        return report
    if document["applies_to"] != expected:
        report["reason"] = "applicability_mismatch"
        return report
    report["scope_match"] = "declared_match"
    state = freshness(document, now)
    if state != "fresh":
        report["reason"] = "declaration_freshness_" + state
        return report
    mechanisms = document["mechanisms"]
    tuples = [identity(item) for item in mechanisms.values()]
    if len(set(tuples)) != len(tuples):
        report["reason"] = "ambiguous_mechanism_identity"
        return report
    known = {identity(item) for item in vocabulary["recognized_tuples"]}
    for key, item in mechanisms.items():
        report["mechanisms"][key] = {
            field: item[field] for field in (*IDENTITY_FIELDS, "roles", "support")}
        report["mechanisms"][key].update(
            vocabulary_match=identity(item) in known,
            independent_testing="unverified" if "test_report" in item else "not_supplied",
            endpoint_uris=item.get("endpoint_uris", []),
            documentation_uris=item.get("documentation_uris", []))
    unresolved = False
    for group in document["requirements"]:
        keys = group["mechanisms"]
        if any(key not in mechanisms for key in keys):
            report["reason"] = "requirement_reference_unresolved"
            return report
        understood = [identity(mechanisms[key]) in known
                      and mechanisms[key]["support"] == "supported" for key in keys]
        interpretable = any(understood) if group["mode"] == "one_of" else all(understood)
        report["requirements"].append({"mode": group["mode"], "mechanisms": keys,
                                       "interpretation": "described" if interpretable else "unresolved"})
        unresolved = unresolved or not interpretable
    if unresolved:
        report["reason"] = "required_mechanism_unresolved"
    elif not mechanisms:
        report["reason"] = "support_not_declared"
    else:
        report.update(state="declarations_read", reason="declarations_are_not_authority")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--declaration-file", required=True)
    parser.add_argument("--expected-context-file", required=True)
    parser.add_argument("--known-vocabulary-file", required=True,
                        help="Fictional recognition vocabulary, not installed adapters")
    parser.add_argument("--at", help="Offline fixture timestamp only")
    args = parser.parse_args(argv)
    try:
        report = illustrate(read_file(args.declaration_file), read_file(args.expected_context_file),
                            read_file(args.known_vocabulary_file),
                            timestamp(args.at) if args.at else datetime.now(timezone.utc))
    except ConsumerError as exc:
        # The CLI does not identify any read failure as an absent capability.
        report = {"illustration": "protocol-support-reader/0.1", "state": "unresolved",
                  "reason": str(exc), "access_granted": False, "approval_granted": False,
                  "caller_eligibility": "unresolved", "interoperability_verified": False,
                  "runtime_enforcement_performed": False, "requirements_satisfied": False}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == "declarations_read" else 1


if __name__ == "__main__":
    raise SystemExit(main())
