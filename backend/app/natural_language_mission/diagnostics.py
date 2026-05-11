"""Diagnostic helpers.

The platform is **not safety-certified**. These helpers normalise
how diagnostics are aggregated, deduplicated, and serialised. The
compiler treats diagnostics as first-class outputs.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .models import (
    Diagnostic,
    SEVERITY_INFO,
    SEVERITY_REJECTION,
    SEVERITY_WARNING,
)


def merge(*streams: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    out: list[Diagnostic] = []
    seen: set[tuple[str, str, str, str]] = set()
    for stream in streams:
        for d in stream:
            key = (d.code, d.message, d.clause, d.field)
            if key in seen:
                continue
            seen.add(key)
            out.append(d)
    return tuple(out)


def has_rejection(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(d.severity == SEVERITY_REJECTION for d in diagnostics)


def has_warning(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(d.severity == SEVERITY_WARNING for d in diagnostics)


def to_dicts(diagnostics: Iterable[Diagnostic]) -> list[dict]:
    return [asdict(d) for d in diagnostics]


__all__ = [
    "merge",
    "has_rejection",
    "has_warning",
    "to_dicts",
    "SEVERITY_INFO",
    "SEVERITY_WARNING",
    "SEVERITY_REJECTION",
]
