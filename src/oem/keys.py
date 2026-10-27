"""Ed25519 keys for signing ledger records.

The private key never enters a ledger, a repository or a log. Only the public
key and its identifier (``key_id``) are recorded, and verifiers decide which
keys they trust through a ``trust.json`` file they control.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"), validate=True)


def key_id_for(public_raw: bytes) -> str:
    """Short, stable identifier for a public key (first 16 hex of SHA-256)."""
    return hashlib.sha256(public_raw).hexdigest()[:16]


@dataclass(frozen=True)
class Signer:
    private_key: Ed25519PrivateKey

    @property
    def public_raw(self) -> bytes:
        return self.private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )

    @property
    def key_id(self) -> str:
        return key_id_for(self.public_raw)

    @property
    def public_b64(self) -> str:
        return _b64(self.public_raw)

    def sign(self, message: bytes) -> str:
        return _b64(self.private_key.sign(message))

    @classmethod
    def generate(cls) -> "Signer":
        return cls(Ed25519PrivateKey.generate())

    def save(self, path: Path) -> None:
        """Write the private key (PEM, unencrypted) with owner-only permissions."""
        pem = self.private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(pem)

    @classmethod
    def load(cls, path: Path) -> "Signer":
        key = serialization.load_pem_private_key(path.read_bytes(), password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise ValueError(f"{path} is not an Ed25519 private key")
        return cls(key)


def verify_signature(public_b64: str, message: bytes, signature_b64: str) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(_unb64(public_b64)).verify(
            _unb64(signature_b64), message
        )
        return True
    except (InvalidSignature, ValueError):
        return False


@dataclass(frozen=True)
class TrustStore:
    """Public keys a verifier accepts, keyed by ``key_id``."""

    keys: dict[str, dict]

    def public_for(self, key_id: str) -> str | None:
        entry = self.keys.get(key_id)
        return entry["public"] if entry else None

    @classmethod
    def load(cls, path: Path) -> "TrustStore":
        data = json.loads(path.read_text(encoding="utf-8"))
        keys = {}
        for entry in data.get("keys", []):
            if key_id_for(_unb64(entry["public"])) != entry["key_id"]:
                raise ValueError(f"trust entry {entry['key_id']}: key_id does not match key")
            keys[entry["key_id"]] = entry
        return cls(keys)

    @staticmethod
    def entry(signer: Signer, owner: str, role: str) -> dict:
        return {
            "key_id": signer.key_id,
            "public": signer.public_b64,
            "owner": owner,
            "role": role,
        }
