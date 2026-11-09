"""Run the portable positive/negative signing corpus offline; no network operations."""
import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.signing.atm_signing import VerificationError, verify


def inputs(directory, vector, overrides=None):
    overrides = overrides or {}
    return (
        bytes.fromhex(overrides['payload_hex']) if 'payload_hex' in overrides else (directory / vector['payload']).read_bytes(),
        bytes.fromhex(overrides['signature_hex']) if 'signature_hex' in overrides else (directory / vector['signature']).read_bytes(),
        bytes.fromhex(overrides['jwks_hex']) if 'jwks_hex' in overrides else (directory / vector['jwks']).read_bytes(),
        overrides.get('origin', vector['origin']), overrides.get('type', vector['type']),
        overrides.get('now', vector['now']),
    )


def check(directory):
    corpus = json.loads((directory / 'vectors.json').read_bytes())
    bases = {v['payload']: v for v in corpus['vectors']}
    for vector in bases.values():
        verify(*inputs(directory, vector))
    failures = []
    for case in corpus['negative_vectors']:
        try:
            verify(*inputs(directory, bases[case['base_vector']], case['overrides']))
            reason = 'unexpected_success'
        except VerificationError as exc:
            reason = str(exc)
        if reason != case['expected_reason']:
            failures.append({'id': case['id'], 'expected': case['expected_reason'], 'actual': reason})
    return {'positive': len(bases), 'negative': len(corpus['negative_vectors']),
            'passed': not failures, 'failures': failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'examples/signing')
    args = parser.parse_args()
    result = check(args.directory)
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
