"""Shared helpers for the live-runtime probe CLIs.

Every probe under ``rover_ws/tools/`` follows the same pattern:

* try to import ``rclpy``; remember whether it is available;
* accept ``--static-only`` to force the offline path;
* run static checks (always available; backed by
  :mod:`app.runtime_validation.static_validator`);
* if running in live mode, run the live ROS-side checks; otherwise
  emit ``not_executed`` for the live-only checks with an explicit
  reason;
* write JSON + Markdown evidence into the configured run directory;
* return a :class:`ProbeOutcome` with the canonical status vocabulary.

Probes never claim ``passed`` for live checks they did not actually
execute. Static-only mode is always honest.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path


def ensure_app_on_path() -> None:
    """Make :mod:`app` importable when the probe is run from anywhere.

    The probes live under ``rover_ws/tools/`` but reuse
    :mod:`app.runtime_validation` and :mod:`app.verification` from
    ``backend/``. This helper inserts ``backend/`` at the head of
    ``sys.path`` so the imports resolve without a prior
    ``pip install``.
    """

    here = Path(__file__).resolve()
    repo_root = here.parents[2]
    backend = repo_root / "backend"
    candidates = (
        backend,
        repo_root,
    )
    for cand in candidates:
        if cand.exists() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))


ensure_app_on_path()


def detect_rclpy() -> tuple[bool, str]:
    """Return ``(available, reason)`` for live-mode availability.

    The reason is empty when ROS is available; otherwise it explains
    the gap so the report can surface it.
    """

    try:
        import rclpy  # type: ignore  # noqa: F401
    except ImportError as exc:
        return False, f"rclpy not importable: {exc}"
    if shutil.which("ros2") is None:
        return False, "ros2 CLI not on PATH"
    return True, ""


def detect_gazebo() -> tuple[bool, str]:
    """Best-effort Gazebo-Harmonic-availability check."""

    if shutil.which("gz") is None:
        return False, "`gz` CLI not on PATH (Gazebo Harmonic missing)"
    return True, ""


def common_argparser(*, description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=Path("evidence/runtime"),
        help="root directory under which evidence/<run_id>/ is written",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default="",
        help="run identifier; empty => generated from timestamp",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repository root (defaults to two levels above the tools dir)",
    )
    parser.add_argument(
        "--static-only",
        action="store_true",
        help="skip live ROS / Gazebo checks even if available",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON to stdout in addition to the evidence file",
    )
    return parser


@dataclass
class ProbeOutcome:
    name: str
    mode: str
    """One of ``live``, ``static-only``, ``not_executed``."""

    status: str
    detail: str = ""
    reason: str = ""
    artefact_paths: list[str] = field(default_factory=list)
    payload: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "mode": self.mode,
            "status": self.status,
            "detail": self.detail,
            "reason": self.reason,
            "artefact_paths": list(self.artefact_paths),
            "payload": dict(self.payload),
        }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def emit(outcome: ProbeOutcome, *, as_json: bool) -> int:
    if as_json:
        json.dump(outcome.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"[{outcome.status}] {outcome.name} ({outcome.mode}) — {outcome.detail}")
        if outcome.reason:
            print(f"  reason: {outcome.reason}")
        for path in outcome.artefact_paths:
            print(f"  evidence: {path}")
    return 0 if outcome.status == "passed" else 1
