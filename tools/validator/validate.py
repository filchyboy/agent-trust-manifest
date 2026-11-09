#!/usr/bin/env python3
"""Local structural validation; optional format checks are not trust verification."""
import argparse
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import SchemaError
    from referencing import Registry, Resource
    from referencing.exceptions import Unresolvable
except ImportError:
    print("Install dependencies first: python -m pip install -r requirements.txt", file=sys.stderr)
    sys.exit(2)


def load_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate object key: {key}")
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f"non-JSON constant: {value}")

    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=pairs, parse_constant=constant)


def check_schema(schema):
    if not isinstance(schema, dict) or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("only object schemas declaring JSON Schema draft 2020-12 are supported")
    Draft202012Validator.check_schema(schema)


def build_registry(schema_dir):
    resources = []
    for path in sorted(schema_dir.glob("*.schema.json")):
        schema = load_json(path)
        check_schema(schema)
        resource = Resource.from_contents(schema)
        resources.append((path.as_uri(), resource))
        if schema.get("$id"):
            resources.append((schema["$id"], resource))
    # No retrieve callback: unknown references never cause network requests.
    return Registry().with_resources(resources)


def pointer(path):
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1")
                           for part in path) if path else "<root>"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--structural-only", action="store_true", help="explicitly select the existing structural-only default")
    modes.add_argument("--strict-formats", action="store_true",
                        help="also check schema format annotations; not full conformance or authenticity")
    parser.add_argument("document")
    parser.add_argument("schema")
    args = parser.parse_args(argv)
    document_path, schema_path = Path(args.document).resolve(), Path(args.schema).resolve()
    try:
        document, schema = load_json(document_path), load_json(schema_path)
        check_schema(schema)
        registry = build_registry(schema_path.parent)
        # Give anonymous local roots a base URI for relative local references.
        schema = dict(schema)
        schema.setdefault("$id", schema_path.as_uri())
        checker = FormatChecker() if args.strict_formats else None
        if checker is not None and not {"uri", "date-time"} <= set(checker.checkers):
            raise ValueError("strict formats require dependencies from requirements.txt")
        validator = Draft202012Validator(schema, registry=registry, format_checker=checker)
        errors = sorted(validator.iter_errors(document),
                        key=lambda error: (pointer(error.absolute_path), error.message))
    except (OSError, ValueError, RecursionError, SchemaError, Unresolvable) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        print(f"INVALID: {document_path}", file=sys.stderr)
        for error in errors:
            print(f"  {pointer(error.absolute_path)}: {error.message}", file=sys.stderr)
        return 1
    mode = "structure and formats" if args.strict_formats else "structure only"
    print(f"VALID ({mode}): {document_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
