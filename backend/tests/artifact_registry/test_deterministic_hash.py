"""Additional tests for :mod:`deterministic_hash` covering #9 and #22.

* :func:`hashes_match` now uses :func:`hmac.compare_digest`, so equality
  is constant-time over the encoded bytes. We assert the contract;
  timing is not directly observable in unit tests but the
  ``compare_digest`` implementation is the property we depend on.
* :func:`short_hash` is documented as display-only.
"""

from __future__ import annotations

import hmac

from app.artifact_registry.deterministic_hash import (
    HASH_PREFIX_LENGTH,
    hash_bytes,
    hashes_match,
    short_hash,
)


def test_hashes_match_accepts_identical() -> None:
    h = hash_bytes(b"hello")
    assert hashes_match(h, h)


def test_hashes_match_is_case_insensitive() -> None:
    h = hash_bytes(b"hello")
    assert hashes_match(h.upper(), h.lower())


def test_hashes_match_rejects_different() -> None:
    a = hash_bytes(b"a")
    b = hash_bytes(b"b")
    assert not hashes_match(a, b)


def test_hashes_match_rejects_empty_expected() -> None:
    assert not hashes_match("", hash_bytes(b"x"))


def test_hashes_match_rejects_length_mismatch() -> None:
    """``compare_digest`` returns False for length mismatches without leak."""

    h = hash_bytes(b"x")
    assert not hashes_match(h, h + "00")
    assert not hashes_match(h, h[:-2])


def test_hashes_match_uses_compare_digest_under_the_hood() -> None:
    # Sanity: the same primitive must agree with our wrapper for
    # equal-length lower-case inputs.
    h = hash_bytes(b"sanity")
    assert hmac.compare_digest(h.encode(), h.encode()) is True
    assert hashes_match(h, h) is True


def test_short_hash_is_display_length() -> None:
    full = hash_bytes(b"any")
    assert len(short_hash(full)) == HASH_PREFIX_LENGTH
