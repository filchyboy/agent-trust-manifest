"""Validate the curated local examples; strict formats are an explicit author/CI option."""
import argparse
import json
from pathlib import Path
import sys

if __package__ in (None,''): sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.validator.validate import main as validate
ROOT=Path(__file__).resolve().parents[2]


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--strict-formats',action='store_true')
    mode.add_argument('--structural-only',action='store_true')
    args=parser.parse_args(argv)
    cases=json.loads((Path(__file__).with_name('example-cases.json')).read_bytes())['cases']
    failures=0
    for case in cases:
        options=['--strict-formats'] if args.strict_formats else ['--structural-only']
        failures += bool(validate([*options,str(ROOT/case['document']),str(ROOT/case['schema'])]))
    print(json.dumps({'examples':len(cases),'mode':'strict-formats' if args.strict_formats else 'structural-only','failures':failures}))
    return 1 if failures else 0


if __name__=='__main__': raise SystemExit(main())
