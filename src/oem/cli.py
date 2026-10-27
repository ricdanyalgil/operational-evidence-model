"""Command line: keys, the research ledger, and a tamper demonstration."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from . import __version__
from .keys import Signer, TrustStore
from .ledger import Ledger, verify

DEFAULT_KEY = Path.home() / ".oem" / "signing.key"


def _cmd_keygen(args: argparse.Namespace) -> int:
    path = Path(args.out)
    if path.exists() and not args.force:
        print(f"{path} exists; use --force to replace it", file=sys.stderr)
        return 1
    signer = Signer.generate()
    signer.save(path)
    entry = TrustStore.entry(signer, owner=args.owner, role=args.role)
    print(json.dumps(entry, indent=2))
    print(f"\nPrivate key written to {path} (keep it out of every repository).", file=sys.stderr)
    print("Add the entry above to ledger/trust.json.", file=sys.stderr)
    return 0


def _cmd_append(args: argparse.Namespace) -> int:
    signer = Signer.load(Path(args.key))
    body = json.loads(args.body) if args.body else {}
    if args.title:
        body.setdefault("title", args.title)
    record = Ledger(Path(args.ledger)).append(args.kind, body, signer)
    print(f"appended seq {record['seq']} {record['hash'][:16]}…")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    trust = TrustStore.load(Path(args.trust))
    checkpoint = json.loads(Path(args.checkpoint).read_text()) if args.checkpoint else None
    report = verify(Ledger(Path(args.ledger)).records(), trust, checkpoint)
    print(report.summary())
    return 0 if report.ok else 1


def _cmd_checkpoint(args: argparse.Namespace) -> int:
    print(json.dumps(Ledger(Path(args.ledger)).checkpoint(), indent=2))
    return 0


def _cmd_demo(_: argparse.Namespace) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="oem-demo-"))
    try:
        signer = Signer.generate()
        trust = TrustStore({signer.key_id: TrustStore.entry(signer, "demo", "demo")})
        ledger = Ledger(tmp / "demo.jsonl")
        print("== a sensor writes three records")
        ledger.append("capture", {"sensor": "cam-01", "event": "person detected"}, signer)
        ledger.append("capture", {"sensor": "lidar-02", "event": "motion", "zone": "B"}, signer)
        ledger.append("derived", {"from": [0, 1], "model": "fusion-v0", "alert": "intrusion"}, signer)
        checkpoint = ledger.checkpoint()
        print(verify(ledger.records(), trust, checkpoint).summary())

        print("\n== someone edits record 1 after the fact (zone B -> zone C)")
        original = ledger.path.read_text().splitlines()
        edited = list(original)
        rec = json.loads(edited[1])
        rec["body"]["zone"] = "C"
        edited[1] = json.dumps(rec, sort_keys=True)
        ledger.path.write_text("\n".join(edited) + "\n")
        print(verify(ledger.records(), trust, checkpoint).summary())

        print("\n== instead, the last record is deleted (the chain alone cannot see it)")
        ledger.path.write_text("\n".join(original[:-1]) + "\n")
        print(verify(ledger.records(), trust).summary().splitlines()[-1], "(chain alone)")
        print(verify(ledger.records(), trust, checkpoint).summary(), "(with checkpoint)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="oem", description=__doc__)
    p.add_argument("--version", action="version", version=f"oem {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    k = sub.add_parser("keygen", help="create an Ed25519 signing key")
    k.add_argument("--out", default=str(DEFAULT_KEY))
    k.add_argument("--owner", required=True)
    k.add_argument("--role", default="researcher")
    k.add_argument("--force", action="store_true")
    k.set_defaults(func=_cmd_keygen)

    a = sub.add_parser("append", help="append a signed record to a ledger")
    a.add_argument("ledger")
    a.add_argument("--kind", required=True)
    a.add_argument("--title")
    a.add_argument("--body", help="JSON object")
    a.add_argument("--key", default=str(DEFAULT_KEY))
    a.set_defaults(func=_cmd_append)

    v = sub.add_parser("verify", help="verify a ledger offline")
    v.add_argument("ledger")
    v.add_argument("--trust", required=True)
    v.add_argument("--checkpoint")
    v.set_defaults(func=_cmd_verify)

    c = sub.add_parser("checkpoint", help="print the ledger head for external anchoring")
    c.add_argument("ledger")
    c.set_defaults(func=_cmd_checkpoint)

    d = sub.add_parser("demo", help="show tamper detection on a throwaway ledger")
    d.set_defaults(func=_cmd_demo)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
