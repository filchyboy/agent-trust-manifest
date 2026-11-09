"""Offline ATM detached JWS signing and verification. Never retrieves keys."""
import argparse
import json
import sys
import time
from pathlib import Path
from atm_signing import MANIFEST, FINDING, VerificationError, sign, verify, require


def read(path, limit=65536):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "file_too_large")
    return raw


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("sign", "verify"):
        s = sub.add_parser(name)
        s.add_argument("--payload", required=True)
        s.add_argument("--origin", required=True)
        s.add_argument("--type", choices=["manifest", "finding"], required=True)
        if name == "sign":
            s.add_argument("--seed-file", required=True, help="Private raw 32-byte Ed25519 seed; never publish")
            s.add_argument("--kid", required=True)
            s.add_argument("--iat", required=True, type=int)
            s.add_argument("--exp", required=True, type=int)
        else:
            s.add_argument("--signature", required=True)
            s.add_argument("--jwks", required=True, help="Explicitly trusted offline key snapshot")
            s.add_argument("--at", type=int, help="Fixture decision time; defaults to current time")
    args = p.parse_args()
    try:
        raw = read(args.payload)
        kind = MANIFEST if args.type == "manifest" else FINDING
        if args.command == "sign":
            sys.stdout.buffer.write(sign(raw, read(args.seed_file, 32), args.origin, kind, args.kid, args.iat, args.exp))
        else:
            h = verify(raw, read(args.signature, 4096), read(args.jwks, 16384), args.origin, kind,
                       int(time.time()) if args.at is None else args.at)
            print(json.dumps({"authentication": "authenticated", "issuer": h["origin"], "claims_truth": "unresolved"}))
        return 0
    except (OSError, VerificationError) as exc:
        print(json.dumps({"authentication": "unverified", "reason": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
