#!/usr/bin/env python3
"""ROS host qualification CLI.

Inspects the host for the runtime stack's prerequisites and writes
``host-qualification.json`` plus ``host-qualification.md`` to the
configured evidence run directory.

Each check returns one of ``passed``, ``failed``, ``partial``,
``skipped``, ``not_executed``. Checks that require ROS or Gazebo are
reported as ``not_executed`` with a reason rather than failing when
the dependency is missing — CI runs without ROS and must remain
green for static-only checks.

Usage:
    rover_ws/tools/qualify_ros_host.py [--evidence-root evidence/host] [--run-id <id>]
                                       [--workspace-root <path>] [--json]
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import (  # noqa: E402  (sys.path mutated)
    ProbeOutcome,
    common_argparser,
    emit,
    ensure_app_on_path,
    write_json,
)

ensure_app_on_path()

from app.runtime_validation.evidence_layout import (  # noqa: E402
    new_runtime_run_id,
)
from app.runtime_validation.host_qualification import (  # noqa: E402
    qualify_host,
    render_host_qualification_md,
)


def main(argv: list[str] | None = None) -> int:
    parser = common_argparser(description=__doc__)
    parser.set_defaults(evidence_root=Path("evidence/host"))
    args = parser.parse_args(argv)

    run_id = args.run_id or new_runtime_run_id(prefix="host")
    run_dir = args.evidence_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    result = qualify_host(workspace_root=args.workspace_root)
    json_path = run_dir / "host-qualification.json"
    md_path = run_dir / "host-qualification.md"
    write_json(json_path, result.as_dict())
    md_path.write_text(render_host_qualification_md(result), encoding="utf-8")

    outcome = ProbeOutcome(
        name="qualify_ros_host",
        mode="static-source" if result.status.value != "passed" else "static-source",
        status=result.status.value,
        detail=(
            f"{sum(1 for c in result.checks if c.status.value == 'passed')} passed, "
            f"{sum(1 for c in result.checks if c.status.value == 'not_executed')} not_executed"
        ),
        reason="",
        artefact_paths=[str(json_path), str(md_path)],
        payload=result.as_dict(),
    )
    return emit(outcome, as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
