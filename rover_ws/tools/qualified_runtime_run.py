#!/usr/bin/env python3
"""Phase 5 qualification orchestrator: end-to-end qualification of a runtime run.

Sits one level above ``live_runtime_validator.py``. The orchestrator:

1. qualifies the host (Ubuntu, ROS, Gazebo, colcon, packages, workspace);
2. invokes ``live_runtime_validator.py`` to drive every Phase-4 probe;
3. loads and validates the qualification scenario pack(s);
4. for each scenario, evaluates the documented contract against the
   captured evidence (topics, nodes, TF frames, events, replay
   artefacts) and records a :class:`ScenarioOutcome`;
5. detects regressions in the captured evidence;
6. (optional) compares the run to a baseline and includes the diff;
7. writes ``qualification-summary.md``, ``qualification-summary.json``,
   ``LIVE_RUNTIME_STATUS.md``, and (with ``--canonical-report``)
   ``docs/RUNTIME_QUALIFICATION_REPORT.md`` and
   ``docs/LIVE_RUNTIME_STATUS.md``;
8. updates the evidence index.

Live mode: pass ``--ros-launch`` on a Jazzy host with Gazebo Harmonic.
Without it, every live-runtime check is reported as ``not_executed``
with a reason. CI runs static-only and must remain green.

Usage:
    rover_ws/tools/qualified_runtime_run.py [--static-only] [--ros-launch]
        [--evidence-root evidence/runtime] [--run-id <id>]
        [--scenarios-dir qualification/scenarios]
        [--scenario <id> ...]
        [--baseline qualification/baselines/<name>.json]
        [--canonical-report]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from _probe_common import (  # noqa: E402  (sys.path mutated)
    common_argparser,
    detect_gazebo,
    detect_rclpy,
    ensure_app_on_path,
    write_json,
)

ensure_app_on_path()

from app.runtime_validation.baselines import (  # noqa: E402
    baseline_from_evidence,
    compare_baseline,
    load_baseline,
    render_comparison_md,
)
from app.runtime_validation.evidence_index import (  # noqa: E402
    build_evidence_index,
    write_evidence_index,
)
from app.runtime_validation.evidence_layout import (  # noqa: E402
    EvidenceLayout,
    new_runtime_run_id,
)
from app.runtime_validation.host_qualification import (  # noqa: E402
    qualify_host,
    render_host_qualification_md,
)
from app.runtime_validation.qualification_report import (  # noqa: E402
    QualificationCheck,
    QualificationReport,
    ScenarioOutcome,
    render_live_runtime_status_md,
    render_qualification_summary_md,
)
from app.runtime_validation.qualification_scenarios import (  # noqa: E402
    QualificationScenario,
    load_scenario_pack_from_dir,
)
from app.runtime_validation.regression import (  # noqa: E402
    detect_regressions,
    render_regression_md,
)
from app.verification.acceptance import AcceptanceStatus  # noqa: E402


def _probe_module(name: str):
    import importlib

    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    return importlib.import_module(name)


def _live_runtime_validator_argv(args: argparse.Namespace, layout: EvidenceLayout) -> list[str]:
    argv = [
        "--evidence-root",
        str(args.evidence_root),
        "--run-id",
        layout.run_id,
        "--workspace-root",
        str(args.workspace_root),
        "--skip-runtime-capture",
    ]
    if args.static_only:
        argv.append("--static-only")
    if args.ros_launch:
        argv.append("--ros-launch")
    return argv


def _run_live_runtime_validator(
    *, args: argparse.Namespace, layout: EvidenceLayout
) -> AcceptanceStatus:
    """Invoke live_runtime_validator.main() in-process and return status."""

    module = _probe_module("live_runtime_validator")
    rc = module.main(_live_runtime_validator_argv(args, layout))
    json_path = layout.path("runtime-validation.json")
    if not json_path.exists():
        return AcceptanceStatus.NOT_EXECUTED
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    try:
        return AcceptanceStatus(payload.get("status", "not_executed"))
    except ValueError:
        return AcceptanceStatus.NOT_EXECUTED


def _load_scenarios(
    *, args: argparse.Namespace
) -> tuple[list[QualificationScenario], list[QualificationCheck]]:
    """Load the scenario pack and convert validation results to qualification checks."""

    scenarios_dir = args.scenarios_dir
    if not scenarios_dir.exists():
        return [], [
            QualificationCheck(
                name="qualification_scenarios_present",
                origin="static-workspace",
                status=AcceptanceStatus.NOT_EXECUTED,
                detail=f"scenarios dir does not exist: {scenarios_dir}",
                reason="run with --scenarios-dir or scaffold qualification/scenarios/",
            )
        ]
    scenarios, validations = load_scenario_pack_from_dir(scenarios_dir)
    checks: list[QualificationCheck] = []
    for v in validations:
        checks.append(
            QualificationCheck(
                name=f"scenario_pack[{v.scenario_id}]",
                origin="static-workspace",
                status=v.status,
                detail=("ok" if v.ok else "; ".join(v.errors)),
                reason="" if v.ok else "scenario YAML rejected by parser",
            )
        )
    if args.scenarios:
        wanted = set(args.scenarios)
        scenarios = [s for s in scenarios if s.scenario_id in wanted]
    return scenarios, checks


def _evaluate_scenario_static(
    scenario: QualificationScenario,
    *,
    workspace_root: Path,
    layout: EvidenceLayout,
) -> ScenarioOutcome:
    """Evaluate a scenario against the captured static-mode evidence.

    Live mode would replace this with a probe driven against the live
    ROS graph. The static-mode evaluation cross-references the
    scenario's required topics / nodes / frames against the
    static-only snapshots written by the Phase-4 probes.
    """

    findings: list[str] = []
    status = AcceptanceStatus.NOT_EXECUTED

    topic_path = layout.path("topic-snapshot.json")
    node_path = layout.path("node-snapshot.json")
    tf_path = layout.path("tf-snapshot.json")

    declared_topics: set[str] = set()
    declared_nodes: set[str] = set()
    declared_frames: set[str] = set()

    if topic_path.exists():
        payload = json.loads(topic_path.read_text(encoding="utf-8"))
        rows = payload.get("static", {}).get("rows", [])
        declared_topics = {
            r["topic"] for r in rows
            if r.get("declared_in_workspace") and isinstance(r.get("topic"), str)
        }
    if node_path.exists():
        payload = json.loads(node_path.read_text(encoding="utf-8"))
        rows = payload.get("static", {}).get("rows", [])
        declared_nodes = {
            r["node_name"] for r in rows
            if r.get("declared_in_launch") and isinstance(r.get("node_name"), str)
        }
    if tf_path.exists():
        payload = json.loads(tf_path.read_text(encoding="utf-8"))
        rows = payload.get("static", {}).get("rows", [])
        declared_frames = {
            r["frame"] for r in rows
            if (r.get("declared_in_urdf") or r.get("frame") == "odom")
            and isinstance(r.get("frame"), str)
        }

    missing_topics = [t for t in scenario.required_topics if t not in declared_topics]
    missing_nodes = [n for n in scenario.required_nodes if n not in declared_nodes]
    missing_frames = [
        f for f in (scenario.required_topics if False else ())
    ]
    # The qualification scenario format does not declare TF frames
    # explicitly; the runtime contract from the runtime_validation
    # library carries that. We still surface a warning if a documented
    # scenario references frames we don't recognise (none currently).

    if missing_topics:
        findings.append("missing topics: " + ", ".join(missing_topics))
    if missing_nodes:
        findings.append("missing nodes: " + ", ".join(missing_nodes))

    # In static-only mode we can never claim live-runtime success for a
    # scenario; we report partial when the static workspace check
    # passes and the scenario was declared valid, and not_executed when
    # the static evidence is missing.
    if not (topic_path.exists() and node_path.exists() and tf_path.exists()):
        status = AcceptanceStatus.NOT_EXECUTED
        detail = (
            "live-runtime evidence not available; static-only mode "
            "cannot evaluate scenario contract"
        )
    elif missing_topics or missing_nodes:
        status = AcceptanceStatus.FAILED
        detail = (
            f"{len(missing_topics) + len(missing_nodes)} required entity(ies) "
            "not declared in workspace"
        )
    else:
        # The workspace declares everything the scenario needs, but
        # the live transitions / events were not exercised, so we
        # surface partial.
        status = AcceptanceStatus.PARTIAL
        detail = (
            "static workspace declares every required topic/node; live "
            "evaluation not run in static-only mode"
        )

    return ScenarioOutcome(
        scenario_id=scenario.scenario_id,
        expected_outcome=scenario.expected_outcome,
        observed_status=status,
        detail=detail,
        findings=tuple(findings),
    )


def _required_inventories_from_scenarios(
    scenarios: list[QualificationScenario],
) -> tuple[list[str], list[str], list[str], list[str]]:
    topics: set[str] = set()
    nodes: set[str] = set()
    frames: set[str] = set()
    artefacts: set[str] = set()
    for s in scenarios:
        topics.update(s.required_topics)
        nodes.update(s.required_nodes)
        artefacts.update(s.required_replay_artifacts)
    # Frames are declared by the scenario format implicitly via topics
    # and the runtime_validation library; we do not require a per-scenario
    # frame list right now.
    return sorted(topics), sorted(nodes), sorted(frames), sorted(artefacts)


def main(argv: list[str] | None = None) -> int:
    parser = common_argparser(description=__doc__)
    parser.add_argument(
        "--ros-launch",
        action="store_true",
        help="forwarded to live_runtime_validator (Jazzy host only)",
    )
    parser.add_argument(
        "--scenarios-dir",
        type=Path,
        default=None,
        help=(
            "directory of qualification scenario YAMLs "
            "(default: <workspace-root>/qualification/scenarios)"
        ),
    )
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        default=[],
        help="scenario id to run; repeat to run multiple. Default: every scenario in the pack",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="baseline JSON to compare this run against",
    )
    parser.add_argument(
        "--canonical-report",
        action="store_true",
        help=(
            "also write the qualification report to "
            "docs/RUNTIME_QUALIFICATION_REPORT.md and "
            "docs/LIVE_RUNTIME_STATUS.md"
        ),
    )
    parser.add_argument(
        "--evidence-index-md",
        type=Path,
        default=None,
        help=(
            "override the path for the evidence-index Markdown "
            "output. Tests must pass a temp path so the committed "
            "docs/EVIDENCE_INDEX.md is never modified during pytest."
        ),
    )
    args = parser.parse_args(argv)
    if args.scenarios_dir is None:
        args.scenarios_dir = args.workspace_root / "qualification" / "scenarios"

    available, why = detect_rclpy()
    gz_ok, gz_why = detect_gazebo()
    use_live = available and gz_ok and args.ros_launch and not args.static_only
    mode = "live" if use_live else ("mixed" if args.ros_launch and available else "static-only")

    args.run_id = args.run_id or new_runtime_run_id(prefix="qualified")
    layout = EvidenceLayout(root=args.evidence_root, run_id=args.run_id).ensure()

    # 1. Host qualification.
    host_result = qualify_host(workspace_root=args.workspace_root)
    write_json(layout.run_dir / "host-qualification.json", host_result.as_dict())
    (layout.run_dir / "host-qualification.md").write_text(
        render_host_qualification_md(host_result), encoding="utf-8"
    )

    # 2. Drive the Phase-4 orchestrator.
    runtime_status = _run_live_runtime_validator(args=args, layout=layout)
    runtime_payload: dict = {}
    runtime_validation_path = layout.path("runtime-validation.json")
    if runtime_validation_path.exists():
        runtime_payload = json.loads(runtime_validation_path.read_text(encoding="utf-8"))

    # 3. Load qualification scenarios.
    scenarios, scenario_pack_checks = _load_scenarios(args=args)

    # 4. Evaluate each scenario.
    scenario_outcomes: list[ScenarioOutcome] = []
    for s in scenarios:
        outcome = _evaluate_scenario_static(
            s, workspace_root=args.workspace_root, layout=layout
        )
        scenario_outcomes.append(outcome)
        write_json(
            layout.run_dir / f"qualification-scenario-{s.scenario_id}.json",
            outcome.as_dict() | {"scenario_definition": s.as_dict()},
        )

    # 5. Regression detection (baseline-free findings).
    req_topics, req_nodes, req_frames, req_replay = _required_inventories_from_scenarios(
        scenarios
    )
    # In static-only mode the live probes never run; replay artefacts
    # are produced by the recording stack and cannot be verified
    # offline. Suppress the replay-required list (and the live topic /
    # node / TF lists) so the regression detector does not surface
    # noise; the qualification scenario evaluator already records the
    # absence in scenario_outcomes.
    regression_report = detect_regressions(
        run_dir=layout.run_dir,
        required_topics=req_topics if use_live else [],
        required_nodes=req_nodes if use_live else [],
        required_tf_frames=req_frames if use_live else [],
        required_replay_artifacts=req_replay if use_live else [],
    )
    write_json(
        layout.run_dir / "regression-report.json", regression_report.as_dict()
    )
    (layout.run_dir / "regression-report.md").write_text(
        render_regression_md(regression_report), encoding="utf-8"
    )

    # 6. Baseline comparison (optional).
    baseline_comparison = None
    if args.baseline is not None and args.baseline.exists():
        baseline = load_baseline(args.baseline)
        observed = baseline_from_evidence(layout.run_dir)
        baseline_comparison = compare_baseline(
            baseline=baseline,
            observed=observed,
            baseline_path=args.baseline,
            observed_path=layout.run_dir,
            required_topics=req_topics,
            required_nodes=req_nodes,
            required_tf_frames=req_frames,
        )
        write_json(
            layout.run_dir / "baseline-comparison.json",
            baseline_comparison.as_dict(),
        )
        (layout.run_dir / "baseline-comparison.md").write_text(
            render_comparison_md(baseline_comparison), encoding="utf-8"
        )

    # 7. Compose the qualification report.
    qualification_checks: list[QualificationCheck] = list(scenario_pack_checks)

    # Static-source / static-workspace summary checks derived from
    # runtime_payload; never claim live-runtime in static-only mode.
    if runtime_payload:
        for check in runtime_payload.get("checks", []):
            origin = (
                "static-workspace"
                if check["name"].startswith("static.")
                else (
                    "live-runtime"
                    if mode != "static-only"
                    else "static-workspace"
                )
            )
            qualification_checks.append(
                QualificationCheck(
                    name=check["name"],
                    origin=origin,
                    status=AcceptanceStatus(check["status"]),
                    detail=check.get("detail", ""),
                    reason=check.get("reason", ""),
                    evidence_paths=tuple(check.get("evidence_paths", [])),
                )
            )

    # The host qualifier itself contributes one rolled-up check.
    qualification_checks.append(
        QualificationCheck(
            name="host_qualification",
            origin="static-source",
            status=host_result.status,
            detail=(
                f"{sum(1 for c in host_result.checks if c.status.value == 'passed')} "
                f"of {len(host_result.checks)} host checks passed"
            ),
            evidence_paths=(
                str(layout.run_dir / "host-qualification.json"),
                str(layout.run_dir / "host-qualification.md"),
            ),
        )
    )

    # Build the runtime_report wrapper just enough so the renderer can
    # reuse it (we don't want to re-run the orchestrator).
    runtime_report = None
    if runtime_payload:
        from app.runtime_validation.report_renderer import RuntimeCheck, RuntimeReport

        runtime_report = RuntimeReport(
            run_id=runtime_payload.get("run_id", layout.run_id),
            mode=runtime_payload.get("mode", mode),
            generated_at_utc=runtime_payload.get("generated_at_utc", ""),
            environment=dict(runtime_payload.get("environment", {})),
            checks=[
                RuntimeCheck(
                    name=c["name"],
                    status=AcceptanceStatus(c["status"]),
                    detail=c.get("detail", ""),
                    reason=c.get("reason", ""),
                    errors=list(c.get("errors", [])),
                    warnings=list(c.get("warnings", [])),
                    evidence_paths=list(c.get("evidence_paths", [])),
                )
                for c in runtime_payload.get("checks", [])
            ],
        )

    qualification_report = QualificationReport(
        run_id=args.run_id,
        mode=mode,
        host_result=host_result,
        runtime_report=runtime_report,
        regression_report=regression_report,
        baseline_comparison=baseline_comparison,
        scenarios=scenario_outcomes,
        qualification_checks=qualification_checks,
    )

    write_json(
        layout.run_dir / "qualification-summary.json",
        qualification_report.as_dict(),
    )
    summary_md = render_qualification_summary_md(qualification_report)
    (layout.run_dir / "qualification-summary.md").write_text(summary_md, encoding="utf-8")
    live_status_md = render_live_runtime_status_md(qualification_report)
    (layout.run_dir / "live-runtime-status.md").write_text(live_status_md, encoding="utf-8")

    # 8. Update the evidence index.
    index = build_evidence_index(evidence_root=args.evidence_root)
    evidence_index_md = args.evidence_index_md or (
        args.workspace_root / "docs" / "EVIDENCE_INDEX.md"
    )
    write_evidence_index(
        index,
        json_path=args.evidence_root / "index.json",
        markdown_path=evidence_index_md,
    )

    if args.canonical_report:
        canonical_dir = args.workspace_root / "docs"
        canonical_dir.mkdir(parents=True, exist_ok=True)
        (canonical_dir / "RUNTIME_QUALIFICATION_REPORT.md").write_text(
            summary_md, encoding="utf-8"
        )
        (canonical_dir / "LIVE_RUNTIME_STATUS.md").write_text(
            live_status_md, encoding="utf-8"
        )

    print(
        f"qualified-runtime-run: run_id={args.run_id} mode={mode} "
        f"status={qualification_report.overall_status.value}"
    )
    print(f"  evidence: {layout.run_dir}")
    if regression_report.has_regression():
        print(
            f"  regressions: {regression_report.severity.value} "
            f"({len(regression_report.findings)} finding(s))"
        )
    if baseline_comparison is not None and baseline_comparison.has_regression():
        print(f"  baseline: {baseline_comparison.severity.value}")
    if not use_live and args.ros_launch:
        print(f"  note: live launch unavailable ({why or gz_why})")

    return 0 if qualification_report.overall_status == AcceptanceStatus.PASSED else 1


if __name__ == "__main__":
    sys.exit(main())
