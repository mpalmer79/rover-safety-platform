#!/usr/bin/env python3
"""Audit operator replay-review completion.

Per-incident: reads the optional ``review-audit.json`` artefact from
the bundle directory and prints / writes the resulting completion
status. Completion is recognised **only** when the file declares it
explicitly; the auditor never infers completion from any other
artefact.

Usage:
    rover_ws/tools/audit_replay_reviews.py
        [--incident incidents/<incident_id>]
        [--incidents-root incidents]
        [--md-out incidents/<incident_id>/review-audit.md]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.replay_analytics.loader import (  # noqa: E402
    load_replay_bundle,
    load_replay_bundles,
)
from app.replay_analytics.review_audit import (  # noqa: E402
    audit_review,
    write_review_audit_json,
    write_review_audit_md,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incident", type=Path, default=None)
    parser.add_argument("--incidents-root", type=Path, default=Path("incidents"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.incident is not None:
        bundles = [load_replay_bundle(args.incident)]
    else:
        bundles = load_replay_bundles(args.incidents_root)
    if not bundles:
        sys.stderr.write("no incident bundles found\n")
        return 0

    payload: list[dict] = []
    for bundle in bundles:
        audit = audit_review(bundle)
        write_review_audit_json(audit, path=bundle.incident_dir / "review-audit.json")
        write_review_audit_md(audit, path=bundle.incident_dir / "review-audit.md")
        payload.append(audit.as_dict())

    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for row in payload:
            print(
                f"  {row['incident_id']:<35s} status={row['status']:<14s} "
                f"completed={len(row['completed_steps'])} "
                f"pending={len(row['pending_steps'])}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
