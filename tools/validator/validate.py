#!/usr/bin/env python3
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Install jsonschema first: python -m pip install jsonschema", file=sys.stderr)
    sys.exit(2)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_store(schema_dir: Path):
    store = {}
    for schema_file in schema_dir.glob("*.schema.json"):
        schema = load_json(schema_file)
        store[schema_file.name] = schema
        schema_id = schema.get("$id")
        if schema_id:
            store[schema_id] = schema
    return store


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: validate.py <document.json> <schema.json>", file=sys.stderr)
        return 2

    document_path = Path(sys.argv[1]).resolve()
    schema_path = Path(sys.argv[2]).resolve()

    document = load_json(document_path)
    schema = load_json(schema_path)
    store = build_store(schema_path.parent)

    resolver = jsonschema.validators.RefResolver(
        base_uri=schema_path.parent.as_uri() + "/",
        referrer=schema,
        store=store,
    )

    try:
        jsonschema.validate(instance=document, schema=schema, resolver=resolver)
    except jsonschema.ValidationError as exc:
        print(f"INVALID: {document_path}\n{exc.message}", file=sys.stderr)
        return 1

    print(f"VALID: {document_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
