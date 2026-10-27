"""Append-only, hash-chained and signed ledger.

Each line of a ledger file is one JSON record::

    {"v": 1, "seq": 7, "ts": "...", "kind": "...", "body": {...},
     "prev": "<hash of record 6>", "key_id": "...", "hash": "...", "sig": "..."}

``hash`` is SHA-256 over the canonical form of the record without ``hash`` and
``sig``; ``sig`` is an Ed25519 signature over the bytes of ``hash``. Changing,
deleting, reordering or inserting a record breaks a hash, a ``prev`` link or a
signature, and verification reports the first record where that happens.

Two attacks the chain cannot see on its own (the same limit every hash-chained
log has): cutting off the tail, and re-writing the whole file with a key the
verifier trusts. Both are caught only against a *checkpoint* held somewhere the
writer cannot change it, which is why ``checkpoint()`` exists and why the
research ledger of this repository is anchored outside it (see ledger/README.md).
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .canonical import canonical_bytes
from .keys import Signer, TrustStore, verify_signature

FORMAT_VERSION = 1
GENESIS_PREV = "0" * 64


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_hash(record: dict) -> str:
    unsigned = {k: v for k, v in record.items() if k not in ("hash", "sig")}
    return hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


# --- Merkle tree (RFC 6962 hashing) -----------------------------------------

def _leaf(data: bytes) -> bytes:
    return hashlib.sha256(b"\x00" + data).digest()


def _node(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def merkle_root(leaves: list[bytes]) -> str:
    """RFC 6962 Merkle Tree Hash over ``leaves`` (raw bytes), as hex."""

    def mth(items: list[bytes]) -> bytes:
        n = len(items)
        if n == 0:
            return hashlib.sha256(b"").digest()
        if n == 1:
            return _leaf(items[0])
        k = 1
        while k * 2 < n:
            k *= 2
        return _node(mth(items[:k]), mth(items[k:]))

    return mth(leaves).hex()


# --- Ledger -----------------------------------------------------------------

class LedgerCorrupt(RuntimeError):
    """The ledger file cannot be read as a sequence of records."""


@dataclass
class Ledger:
    path: Path

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def append(self, kind: str, body: dict, signer: Signer, ts: str | None = None) -> dict:
        """Append one signed record, under an exclusive lock, and fsync it."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+", encoding="utf-8") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                fh.seek(0)
                last = None
                for n, line in enumerate(fh, start=1):
                    if line.strip():
                        try:
                            last = json.loads(line)
                        except json.JSONDecodeError as exc:
                            # Never repaired silently: a person decides what
                            # happened, and the repair itself is recorded.
                            raise LedgerCorrupt(
                                f"{self.path}: line {n} is not valid JSON (torn write?)"
                            ) from exc
                seq = 0 if last is None else last["seq"] + 1
                prev = GENESIS_PREV if last is None else last["hash"]
                record = {
                    "v": FORMAT_VERSION,
                    "seq": seq,
                    "ts": ts or _now(),
                    "kind": kind,
                    "body": body,
                    "prev": prev,
                    "key_id": signer.key_id,
                }
                record["hash"] = record_hash(record)
                record["sig"] = signer.sign(record["hash"].encode("ascii"))
                fh.seek(0, os.SEEK_END)
                fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
        return record

    def checkpoint(self) -> dict:
        """Head of the ledger, to be stored outside the writer's reach."""
        recs = self.records()
        return {
            "ledger": self.path.name,
            "size": len(recs),
            "head_seq": recs[-1]["seq"] if recs else None,
            "head_hash": recs[-1]["hash"] if recs else GENESIS_PREV,
            "merkle_root": merkle_root([bytes.fromhex(r["hash"]) for r in recs]),
        }


@dataclass
class VerifyReport:
    ok: bool
    checked: int
    failures: list[str] = field(default_factory=list)
    gaps: list[int] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"[{'OK' if self.ok else 'FAIL'}] {self.checked} record(s) checked"]
        lines += [f"        {f}" for f in self.failures]
        if self.gaps:
            lines.append(f"        signed gap(s) at seq {', '.join(map(str, self.gaps))}")
        lines.append(f"Integrity: {'VERIFIED' if self.ok else 'FAILED'}.")
        return "\n".join(lines)


def verify(
    records: Iterable[dict],
    trust: TrustStore,
    checkpoint: dict | None = None,
) -> VerifyReport:
    """Verify a ledger offline against trusted keys and, optionally, a checkpoint."""
    records = list(records)
    failures: list[str] = []
    gaps: list[int] = []
    expected_prev = GENESIS_PREV

    for i, rec in enumerate(records):
        seq = rec.get("seq")
        if seq != i:
            failures.append(f"seq {seq}: expected seq {i} (record missing, inserted or reordered)")
            break
        if rec.get("prev") != expected_prev:
            failures.append(f"seq {seq}: prev does not match the hash of the record before it")
            break
        if record_hash(rec) != rec.get("hash"):
            failures.append(f"seq {seq}: hash does not match the record")
            break
        public = trust.public_for(rec.get("key_id", ""))
        if public is None:
            failures.append(f"seq {seq}: signed by key {rec.get('key_id')} which is not trusted")
            break
        if not verify_signature(public, rec["hash"].encode("ascii"), rec.get("sig", "")):
            failures.append(f"seq {seq}: signature is not valid")
            break
        if rec.get("kind") == "gap":
            gaps.append(seq)
        expected_prev = rec["hash"]

    if not failures and checkpoint is not None:
        size = checkpoint.get("size", 0)
        if len(records) < size:
            failures.append(
                f"ledger has {len(records)} record(s) but the checkpoint saw {size} (tail cut off)"
            )
        else:
            prefix = [bytes.fromhex(r["hash"]) for r in records[:size]]
            if merkle_root(prefix) != checkpoint.get("merkle_root"):
                failures.append("first records do not match the checkpoint (history rewritten)")

    return VerifyReport(ok=not failures, checked=len(records), failures=failures, gaps=gaps)
