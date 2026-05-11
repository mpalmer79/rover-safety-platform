"""Deterministic hashing of artefact files.

Every committed file in a registered artefact has a sha256 hash
recorded in ``spatial-replay/registry/canonical-artifacts.json``.
The hash is computed from the bytes on disk; any change to the
file bytes, including whitespace or trailing newline differences,
shifts the hash.

The hash also feeds the deterministic reproducibility check in
``hydration.py`` — if a hydration pass changes a hash, CI fails
honestly.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


HASH_PREFIX_LENGTH: int = 16
"""Length of the prefix exposed in the registry. The full sha256 is
also stored, but the prefix is what the UI surfaces in the
``DeterministicHashChain`` panel."""


def hash_file(path: Path) -> str:
    """Return the full sha256 hex digest of ``path``.

    Returns an empty string when the file is missing — callers
    interpret an empty hash as ``MISSING`` and downgrade integrity
    accordingly.
    """

    p = Path(path)
    if not p.exists() or not p.is_file():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_bytes(data: bytes) -> str:
    """Return the sha256 hex digest of ``data``."""

    return hashlib.sha256(data).hexdigest()


def short_hash(full_hash: str) -> str:
    """Return the prefix used by the UI."""

    if not full_hash:
        return ""
    return full_hash[:HASH_PREFIX_LENGTH]


def hashes_match(expected: str, computed: str) -> bool:
    """Equality check; both inputs are normalised to lower case."""

    return expected.lower() == computed.lower() and bool(expected)


__all__ = [
    "HASH_PREFIX_LENGTH",
    "hash_bytes",
    "hash_file",
    "hashes_match",
    "short_hash",
]
