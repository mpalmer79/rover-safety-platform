"""Tamper-evident hash chain over recorded events (#13).

The recorder writes each event with a ``prev_event_hash`` field that
points to the SHA-256 of the *previous* event's **canonical bytes** —
the un-chained serialisation, with the event's own
``prev_event_hash`` field deliberately excluded so the hash is not
self-referential.

Canonical bytes for an event dict ``d`` are defined exactly as::

    json.dumps(
        {k: v for k, v in d.items() if k != "prev_event_hash"},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

The recorder maintains the running tip in memory and writes a final
``events_chain_tip`` plus ``events_count`` into ``metadata.json`` at
``finalize`` time. The validator (see
``app.validation.replay_validator``) recomputes the chain to detect
any tampering — flip a byte in any event, delete a middle line,
truncate the file, and the validator emits
``replay_integrity.chain_broken``.

Stdlib-only by design: the recorder must remain dependency-free.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Mapping


GENESIS_HASH: str = "0" * 64
"""The ``prev_event_hash`` value carried by the first event."""

CHAIN_FIELD: str = "prev_event_hash"


def canonical_event_bytes(event: Mapping[str, Any]) -> bytes:
    """Return the canonical bytes used for chain hashing.

    The serialisation deliberately excludes the event's own
    :data:`CHAIN_FIELD` so the hash is not self-referential. Keys are
    sorted, separators are tight, non-ASCII is preserved verbatim.
    """

    stripped = {k: v for k, v in event.items() if k != CHAIN_FIELD}
    return json.dumps(
        stripped, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def hash_canonical(event: Mapping[str, Any]) -> str:
    """Return SHA-256 hex digest (lower-case) of the canonical bytes."""

    return hashlib.sha256(canonical_event_bytes(event)).hexdigest()


def chain_match(expected: str, computed: str) -> bool:
    """Constant-time hex-string comparison for chain hashes."""

    if not expected or not computed:
        return False
    return hmac.compare_digest(expected.lower().encode(), computed.lower().encode())


def is_valid_chain_hex(value: object) -> bool:
    """Return True if ``value`` is a 64-char lower-case hex string."""

    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(c in "0123456789abcdef" for c in value)


__all__ = [
    "CHAIN_FIELD",
    "GENESIS_HASH",
    "canonical_event_bytes",
    "chain_match",
    "hash_canonical",
    "is_valid_chain_hex",
]
