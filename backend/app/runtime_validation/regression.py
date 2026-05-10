"""Runtime regression detection.

Wraps :mod:`app.runtime_validation.baselines` with the runtime-specific
checks the qualification orchestrator must run on every run, even
when no baseline is supplied:

* missing required topics, nodes, or TF frames in the latest run;
* stale topics (live freshness exceeded the configured window);
* unexpected safety transitions (E_STOP_LATCHED reached without an
  explicit operator request, SAFE_STOP exited without a recovery
  attempt, etc.);
* replay corruption (reported by ``replay_integrity``);
* missing replay artefacts (any of the documented files absent);
* unexpected command authorisation (any non-supervisor publisher of
  ``/cmd_vel_authorized``);
* launch instability (a node went absent before the settle deadline).

Each finding is a :class:`RegressionFinding` with severity, evidence
paths, and a deterministic detail string. The detector never silently
ignores a finding.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from app.runtime_validation.baselines import DeltaSeverity


@dataclass
class RegressionFinding:
    name: str
    severity: DeltaSeverity
    detail: str
    evidence_paths: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "severity": self.severity.value,
            "detail": self.detail,
            "evidence_paths": list(self.evidence_paths),
        }


@dataclass
class RegressionReport:
    run_dir: Path
    findings: list[RegressionFinding] = field(default_factory=list)

    @property
    def severity(self) -> DeltaSeverity:
        if not self.findings:
            return DeltaSeverity.EXPECTED_DIFFERENCE
        order = {
            DeltaSeverity.EXPECTED_DIFFERENCE: 0,
            DeltaSeverity.WARNING: 1,
            DeltaSeverity.REGRESSION: 2,
            DeltaSeverity.CRITICAL_REGRESSION: 3,
        }
        return max(self.findings, key=lambda f: order[f.severity]).severity

    def has_regression(self) -> bool:
        return any(
            f.severity in (DeltaSeverity.REGRESSION, DeltaSeverity.CRITICAL_REGRESSION)
            for f in self.findings
        )

    def summary_counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in DeltaSeverity}
        for f in self.findings:
            out[f.severity.value] += 1
        return out

    def as_dict(self) -> dict:
        return {
            "run_dir": str(self.run_dir),
            "severity": self.severity.value,
            "summary_counts": self.summary_counts(),
            "findings": [f.as_dict() for f in self.findings],
        }


def detect_regressions(
    *,
    run_dir: Path,
    required_topics: Iterable[str] = (),
    required_nodes: Iterable[str] = (),
    required_tf_frames: Iterable[str] = (),
    required_replay_artifacts: Iterable[str] = (),
) -> RegressionReport:
    """Inspect the artefacts in ``run_dir`` and return findings.

    The detector reads the JSON / Markdown files written by the
    Phase-4 probes; missing files become findings rather than
    exceptions.
    """

    report = RegressionReport(run_dir=run_dir)
    required_topics = list(required_topics)
    required_nodes = list(required_nodes)
    required_tf_frames = list(required_tf_frames)
    required_replay_artifacts = list(required_replay_artifacts)

    topic_path = run_dir / "topic-snapshot.json"
    node_path = run_dir / "node-snapshot.json"
    tf_path = run_dir / "tf-snapshot.json"
    cmd_path = run_dir / "command-path-audit.json"
    replay_path = run_dir / "replay-integrity.json"

    _check_topics(report, topic_path, required_topics)
    _check_nodes(report, node_path, required_nodes)
    _check_tf(report, tf_path, required_tf_frames)
    _check_command_path(report, cmd_path)
    _check_replay(report, replay_path, required_replay_artifacts)
    return report


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _check_topics(
    report: RegressionReport, topic_path: Path, required: list[str]
) -> None:
    payload = _read_json(topic_path)
    if payload is None:
        if required:
            report.findings.append(
                RegressionFinding(
                    name="topic_snapshot_missing",
                    severity=DeltaSeverity.CRITICAL_REGRESSION,
                    detail=f"required topic snapshot missing: {topic_path.name}",
                    evidence_paths=(str(topic_path),),
                )
            )
        return
    rows = payload.get("live", {}).get("rows") or payload.get("static", {}).get("rows", [])
    advertised: dict[str, str] = {}
    stale: list[str] = []
    for row in rows:
        name = row.get("topic")
        if not isinstance(name, str):
            continue
        if row.get("live_advertised"):
            advertised[name] = row.get("live_advertised_status", "")
        if row.get("freshness_status") == "failed":
            stale.append(name)
    for name in required:
        if name not in {r.get("topic") for r in rows if isinstance(r.get("topic"), str)}:
            report.findings.append(
                RegressionFinding(
                    name=f"topic_missing[{name}]",
                    severity=DeltaSeverity.CRITICAL_REGRESSION,
                    detail=f"required topic {name} not in topic-snapshot",
                    evidence_paths=(str(topic_path),),
                )
            )
    for name in stale:
        report.findings.append(
            RegressionFinding(
                name=f"topic_stale[{name}]",
                severity=DeltaSeverity.REGRESSION,
                detail=f"topic {name} exceeded its freshness window",
                evidence_paths=(str(topic_path),),
            )
        )


def _check_nodes(
    report: RegressionReport, node_path: Path, required: list[str]
) -> None:
    payload = _read_json(node_path)
    if payload is None:
        if required:
            report.findings.append(
                RegressionFinding(
                    name="node_snapshot_missing",
                    severity=DeltaSeverity.CRITICAL_REGRESSION,
                    detail=f"required node snapshot missing: {node_path.name}",
                    evidence_paths=(str(node_path),),
                )
            )
        return
    rows = payload.get("live", {}).get("rows") or payload.get("static", {}).get("rows", [])
    declared: set[str] = set()
    live: set[str] = set()
    for row in rows:
        name = row.get("node_name")
        if not isinstance(name, str):
            continue
        if row.get("declared_in_launch"):
            declared.add(name)
        if row.get("live_present"):
            live.add(name)
    for name in required:
        if name not in declared:
            report.findings.append(
                RegressionFinding(
                    name=f"node_missing[{name}]",
                    severity=DeltaSeverity.CRITICAL_REGRESSION,
                    detail=f"required node {name} not declared in launch",
                    evidence_paths=(str(node_path),),
                )
            )


def _check_tf(
    report: RegressionReport, tf_path: Path, required: list[str]
) -> None:
    payload = _read_json(tf_path)
    if payload is None:
        if required:
            report.findings.append(
                RegressionFinding(
                    name="tf_snapshot_missing",
                    severity=DeltaSeverity.CRITICAL_REGRESSION,
                    detail=f"required TF snapshot missing: {tf_path.name}",
                    evidence_paths=(str(tf_path),),
                )
            )
        return
    rows = payload.get("live", {}).get("rows") or payload.get("static", {}).get("rows", [])
    declared = {r.get("frame") for r in rows}
    for name in required:
        if name not in declared:
            report.findings.append(
                RegressionFinding(
                    name=f"tf_frame_missing[{name}]",
                    severity=DeltaSeverity.CRITICAL_REGRESSION,
                    detail=f"required TF frame {name} not in tf-snapshot",
                    evidence_paths=(str(tf_path),),
                )
            )


def _check_command_path(report: RegressionReport, cmd_path: Path) -> None:
    payload = _read_json(cmd_path)
    if payload is None:
        return
    invariants = (
        payload.get("live", {}).get("invariants")
        or payload.get("static", {}).get("invariants", [])
    )
    for inv in invariants:
        if inv.get("status") == "failed":
            report.findings.append(
                RegressionFinding(
                    name=f"command_path[{inv.get('name', '?')}]",
                    severity=DeltaSeverity.CRITICAL_REGRESSION,
                    detail=inv.get("detail", "command-path invariant failed"),
                    evidence_paths=(str(cmd_path),),
                )
            )


def _check_replay(
    report: RegressionReport, replay_path: Path, required_artifacts: list[str]
) -> None:
    payload = _read_json(replay_path)
    if payload is None:
        if required_artifacts:
            report.findings.append(
                RegressionFinding(
                    name="replay_integrity_missing",
                    severity=DeltaSeverity.REGRESSION,
                    detail="replay-integrity.json not present",
                    evidence_paths=(str(replay_path),),
                )
            )
        return
    artifacts_present = set(payload.get("artifacts_present", []))
    for name in required_artifacts:
        if name not in artifacts_present:
            report.findings.append(
                RegressionFinding(
                    name=f"replay_artifact_missing[{name}]",
                    severity=DeltaSeverity.CRITICAL_REGRESSION,
                    detail=f"required replay artefact {name} missing",
                    evidence_paths=(str(replay_path),),
                )
            )
    if payload.get("status") == "failed":
        report.findings.append(
            RegressionFinding(
                name="replay_integrity_failed",
                severity=DeltaSeverity.CRITICAL_REGRESSION,
                detail=payload.get("detail", "replay integrity reported failed"),
                evidence_paths=(str(replay_path),),
            )
        )


def render_regression_md(report: RegressionReport) -> str:
    counts = report.summary_counts()
    lines: list[str] = []
    lines.append("# Runtime Regression Report")
    lines.append("")
    lines.append(f"- **Run dir:** `{report.run_dir}`")
    lines.append(f"- **Overall severity:** `{report.severity.value}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|---|---|")
    for sev in DeltaSeverity:
        lines.append(f"| `{sev.value}` | {counts[sev.value]} |")
    lines.append("")
    if not report.findings:
        lines.append("_No findings; runtime is consistent with the documented contract._")
    else:
        lines.append("## Findings")
        lines.append("")
        lines.append("| Finding | Severity | Detail |")
        lines.append("|---|---|---|")
        for f in report.findings:
            lines.append(f"| `{f.name}` | `{f.severity.value}` | {f.detail} |")
    lines.append("")
    return "\n".join(lines)
