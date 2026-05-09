#!/usr/bin/env python3
"""Phase 4 live runtime validator: orchestrate every probe in one pass.

The orchestrator:

* runs the four probes in order — ``launch_smoke_test``,
  ``topic_probe``, ``tf_probe``, ``command_path_probe`` — and
  optionally ``runtime_capture`` for one fault scenario;
* aggregates their :class:`ProbeOutcome` reports into a single
  :class:`RuntimeReport` using the Phase-3 status vocabulary;
* writes ``runtime-validation.json``, ``runtime-validation.md``, and
  ``known-limitations.md`` to ``evidence/runtime/<run_id>/``.

In static-only mode the orchestrator is honest: every probe that
requires a live ROS / Gazebo graph is reported as ``not_executed``
with a reason that names the missing dependency.

Usage:
    rover_ws/tools/live_runtime_validator.py [--static-only] [--ros-launch]
        [--evidence-root evidence/runtime] [--run-id <id>]
        [--canonical-report] [--workspace-root <path>]

If ``--canonical-report`` is supplied, the Markdown report is also
written to ``docs/RUNTIME_VALIDATION_REPORT.md``.
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import (  # noqa: E402  (sys.path mutated)
    common_argparser,
    detect_gazebo,
    detect_rclpy,
    ensure_app_on_path,
    write_json,
)

ensure_app_on_path()

from app.runtime_validation.evidence_layout import (  # noqa: E402
    EvidenceLayout,
    new_runtime_run_id,
)
from app.runtime_validation.report_renderer import (  # noqa: E402
    RuntimeCheck,
    RuntimeReport,
    render_known_limitations_md,
    render_runtime_report_md,
)
from app.runtime_validation.static_validator import (  # noqa: E402
    run_static_validation,
)
from app.verification.acceptance import AcceptanceStatus  # noqa: E402


# Probe modules (imported lazily so a probe-import error surfaces in the
# probe's check rather than at orchestrator load).


def _probe_module(name: str):
    import importlib
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    return importlib.import_module(name)


def _status_from_str(value: str) -> AcceptanceStatus:
    try:
        return AcceptanceStatus(value)
    except ValueError:
        return AcceptanceStatus.NOT_EXECUTED


def _evidence_paths_for(layout: EvidenceLayout, names: list[str]) -> list[str]:
    return [str(layout.path(n)) for n in names]


def _detect_environment() -> dict[str, str]:
    rclpy_ok, rclpy_why = detect_rclpy()
    gz_ok, gz_why = detect_gazebo()
    ros_distro = ""
    try:  # pragma: no cover - depends on environment
        result = subprocess.run(
            ["ros2", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            ros_distro = result.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "rclpy_available": "yes" if rclpy_ok else f"no ({rclpy_why})",
        "ros2_cli": shutil.which("ros2") or "not found",
        "ros2_version": ros_distro,
        "gazebo_available": "yes" if gz_ok else f"no ({gz_why})",
    }


def _probe_argv(*, args: argparse.Namespace) -> list[str]:
    """Argv suffix shared by every probe call."""

    out = [
        "--evidence-root",
        str(args.evidence_root),
        "--run-id",
        args.run_id,
        "--workspace-root",
        str(args.workspace_root),
    ]
    if args.static_only:
        out.append("--static-only")
    return out


def _run_probe(
    *,
    name: str,
    module_name: str,
    layout: EvidenceLayout,
    args: argparse.Namespace,
    extra_args: list[str] | None = None,
    evidence_files: list[str],
) -> RuntimeCheck:
    """Run one probe ``main(argv)`` and turn its outcome into a RuntimeCheck.

    The orchestrator imports each probe as a module and calls its
    ``main`` function with a constructed argv. This keeps subprocess
    overhead off the critical path while preserving the probe's CLI
    contract.
    """

    module = _probe_module(module_name)
    argv = _probe_argv(args=args)
    if extra_args:
        argv = argv + extra_args
    argv = argv + ["--json"]

    # Each probe writes its evidence to the layout and prints a JSON
    # outcome to stdout when --json is set. We only care about its
    # exit code + the on-disk artefacts here. We invoke main()
    # directly so the test suite can mock the probe via its module
    # rather than via subprocess.
    import io
    import contextlib

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exit_code = module.main(argv)
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    except Exception as exc:  # pragma: no cover - probe crash
        return RuntimeCheck(
            name=name,
            status=AcceptanceStatus.FAILED,
            detail=f"probe {module_name} crashed",
            errors=[repr(exc)],
            evidence_paths=_evidence_paths_for(layout, evidence_files),
        )

    # The probe wrote a single JSON document to stdout (multi-line,
    # pretty-printed). Decode the buffer as one object; if that fails
    # for any reason, fall back to the exit code.
    import json

    outcome: dict = {}
    raw = buf.getvalue().strip()
    if raw:
        try:
            decoded = json.loads(raw)
            if isinstance(decoded, dict):
                outcome = decoded
        except json.JSONDecodeError:
            pass

    status = _status_from_str(outcome.get("status", "not_executed"))
    if exit_code != 0 and status == AcceptanceStatus.PASSED:
        status = AcceptanceStatus.FAILED
    return RuntimeCheck(
        name=name,
        status=status,
        detail=outcome.get("detail", ""),
        reason=outcome.get("reason", ""),
        evidence_paths=_evidence_paths_for(layout, evidence_files),
    )


def _static_check_to_runtime_check(static_check) -> RuntimeCheck:
    return RuntimeCheck(
        name=f"static.{static_check.name}",
        status=static_check.status,
        detail=static_check.detail,
        reason=(
            "; ".join(static_check.errors)
            if static_check.status == AcceptanceStatus.FAILED
            else (
                "static-only mode: live runtime not exercised"
                if static_check.status == AcceptanceStatus.NOT_EXECUTED
                else ""
            )
        ),
        errors=list(static_check.errors),
        warnings=list(static_check.warnings),
    )


def main(argv: list[str] | None = None) -> int:
    parser = common_argparser(description=__doc__)
    parser.add_argument(
        "--ros-launch",
        action="store_true",
        help="forwarded to launch_smoke_test and runtime_capture",
    )
    parser.add_argument(
        "--scenario",
        default="stale_lidar_restricted_mode",
        help="fault scenario for runtime_capture",
    )
    parser.add_argument(
        "--canonical-report",
        action="store_true",
        help="also write the Markdown report to docs/RUNTIME_VALIDATION_REPORT.md",
    )
    parser.add_argument(
        "--skip-runtime-capture",
        action="store_true",
        help="skip the optional runtime_capture probe",
    )
    args = parser.parse_args(argv)

    available, why = detect_rclpy()
    use_live = available and not args.static_only
    mode = "live" if use_live else "static-only"

    args.run_id = args.run_id or new_runtime_run_id(prefix="runtime")
    layout = EvidenceLayout(root=args.evidence_root, run_id=args.run_id).ensure()

    environment = _detect_environment()

    # Static workspace validation (always runs).
    static_result = run_static_validation(workspace_root=args.workspace_root)
    static_checks = [_static_check_to_runtime_check(c) for c in static_result.checks]

    # Run probes. Each probe writes its own evidence file; we capture
    # the status it emitted and let the report renderer surface
    # ``not_executed`` with the right reason.
    probe_checks: list[RuntimeCheck] = []
    probe_checks.append(
        _run_probe(
            name="launch_smoke_test",
            module_name="launch_smoke_test",
            layout=layout,
            args=args,
            extra_args=(["--ros-launch"] if args.ros_launch else []),
            evidence_files=["node-snapshot.json", "launch-log.txt"],
        )
    )
    probe_checks.append(
        _run_probe(
            name="topic_probe",
            module_name="topic_probe",
            layout=layout,
            args=args,
            evidence_files=["topic-snapshot.json"],
        )
    )
    probe_checks.append(
        _run_probe(
            name="tf_probe",
            module_name="tf_probe",
            layout=layout,
            args=args,
            evidence_files=["tf-snapshot.json", "tf-tree.txt"],
        )
    )
    probe_checks.append(
        _run_probe(
            name="command_path_probe",
            module_name="command_path_probe",
            layout=layout,
            args=args,
            evidence_files=["command-path-audit.json"],
        )
    )
    if not args.skip_runtime_capture:
        capture_extras = [
            "--scenario",
            args.scenario,
        ]
        if args.ros_launch:
            capture_extras.append("--ros-launch")
        capture_check = _run_probe(
            name=f"runtime_capture[{args.scenario}]",
            module_name="runtime_capture",
            layout=layout,
            args=args,
            extra_args=capture_extras,
            evidence_files=[],
        )
        # runtime_capture writes a per-scenario snapshot, not a fixed
        # evidence file; record the path explicitly for the report.
        capture_check.evidence_paths = [
            str(layout.run_dir / f"runtime-capture-{args.scenario}.json")
        ]
        probe_checks.append(capture_check)

    report = RuntimeReport(
        run_id=args.run_id,
        mode=mode,
        environment=environment,
        checks=static_checks + probe_checks,
    )

    json_path = layout.path("runtime-validation.json")
    write_json(json_path, report.as_dict())
    md_path = layout.path("runtime-validation.md")
    md_path.write_text(render_runtime_report_md(report), encoding="utf-8")
    known_path = layout.path("known-limitations.md")
    known_path.write_text(render_known_limitations_md(report), encoding="utf-8")

    if args.canonical_report:
        canonical = args.workspace_root / "docs" / "RUNTIME_VALIDATION_REPORT.md"
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text(render_runtime_report_md(report), encoding="utf-8")

    print(
        f"runtime-validation: run_id={args.run_id} mode={mode} status={report.status.value}"
    )
    print(f"  evidence: {layout.run_dir}")
    if why and not use_live:
        print(f"  rclpy: {why}")
    return 0 if report.status == AcceptanceStatus.PASSED else 1


if __name__ == "__main__":
    sys.exit(main())
