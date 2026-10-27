"""Canonical JSON serialisation.

Every hash and signature in OEM is computed over a canonical byte form, so that
two implementations (or two runs) that hold the same record produce the same
bytes. The rules follow the spirit of RFC 8785 (JCS) for the value types OEM
uses: objects with string keys, arrays, strings, integers, booleans and null.

Floating-point numbers are deliberately rejected. Sensor readings carry units
and precision, and a float's textual form differs between languages; readings
are therefore stored as decimal strings or scaled integers (see docs/model.md).
"""

from __future__ import annotations

import json
from typing import Any


class CanonicalError(ValueError):
    """Raised when a value cannot be canonicalised."""


def _check(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        raise CanonicalError(
            f"{path}: floats are not allowed; use a decimal string or a scaled integer"
        )
    if isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            _check(item, f"{path}[{i}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalError(f"{path}: object keys must be strings")
            _check(item, f"{path}.{key}")
        return
    raise CanonicalError(f"{path}: unsupported type {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Return the canonical UTF-8 encoding of ``value``."""
    _check(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
