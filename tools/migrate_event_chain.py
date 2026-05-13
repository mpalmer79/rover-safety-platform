#!/usr/bin/env python3
"""One-shot migration: add prev_event_hash chain to checked-in events.jsonl.

Run this once after #13 lands to backfill the tamper-evident chain into
every fixture / golden ``events.jsonl`` under ``evidence/``,
``incidents/``, ``spatial-replay/runs/``, and ``backend/tests/fixtures/``.
Also writes ``events_chain_tip`` / ``events_count`` into the
sibling ``metadata.json`` if present.

This script is NOT wired into CI. After this commit the recorder
produces chained events natively; backfilling stale fixtures is a
one-time operation.

Usage::

    python tools/migrate_event_chain.py [--check]

``--check`` reports drift without writing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOTS = (
    REPO_ROOT / "evidence",
    REPO_ROOT / "incidents",
    REPO_ROOT / "spatial-replay" / "runs",
    REPO_ROOT / "backend" / "tests" / "fixtures",
)

CHAIN_FIELD = "prev_event_hash"
GENESIS_HASH = "0" * 64


def _canonical_bytes(d: dict[str, Any]) -> bytes:
    stripped = {k: v for k, v in d.items() if k != CHAIN_FIELD}
    return json.dumps(
        stripped, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _hash(d: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(d)).hexdigest()


def _migrate_one(path: Path, *, check: bool) -> tuple[bool, str]:
    """Return (drift, message)."""

    lines = path.read_text(encoding="utf-8").splitlines()
    events: list[dict[str, Any]] = []
    for ln, raw in enumerate(lines, start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            events.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            return True, f"{path}:{ln} JSON decode failed: {exc}"
    if not events:
        return False, f"{path}: empty, skipped"

    new_lines: list[str] = []
    tip = GENESIS_HASH
    drift = False
    for d in events:
        prev = d.get(CHAIN_FIELD)
        d[CHAIN_FIELD] = tip
        new_lines.append(
            json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        )
        if prev != tip:
            drift = True
        tip = _hash(d)

    if check:
        return drift, f"{path}: {'drift' if drift else 'ok'} (count={len(events)})"

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Update sibling metadata.json with chain tip + count.
    meta_path = path.parent / "metadata.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return drift, f"{path}: rewritten but metadata.json invalid; skipped tip update"
        meta["events_chain_tip"] = tip
        meta["events_count"] = len(events)
        meta_path.write_text(
            json.dumps(meta, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return drift, f"{path}: rewritten (count={len(events)}, metadata updated)"
    return drift, f"{path}: rewritten (count={len(events)}, no sibling metadata.json)"


def _iter_events_jsonl(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("events.jsonl")):
            yield p


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without rewriting files.",
    )
    args = parser.parse_args()

    any_drift = False
    for path in _iter_events_jsonl(SEARCH_ROOTS):
        drift, msg = _migrate_one(path, check=args.check)
        print(msg)
        any_drift = any_drift or drift

    if args.check and any_drift:
        print("DRIFT: at least one events.jsonl has stale chain.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
