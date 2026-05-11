"""Phase 13 live-runtime tests.

The platform is **not safety-certified**. These tests exercise the
honesty rules that the live-runtime package enforces; they do not
require ROS, Gazebo, Foxglove, or a real bag.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import pytest

from app.live_runtime import (
    BAG_STATUS_BAG_BACKED,
    BAG_STATUS_INVALID,
    BAG_STATUS_MISSING_BAG,
    BAG_STATUS_NOT_EXECUTED,
    BAG_STATUS_PARTIAL,
    LIVE_RUN_STATUS_NOT_EXECUTED,
    LIVE_RUN_STATUS_PASSED,
    LIVE_RUNTIME_DISCLAIMER,
    REQUIRED_EVIDENCE_FILES,
    BagManifest,
    LiveRunSummary,
    RunnerProfile,
    aggregate_maturity,
    bag_manifest_from_dict,
    bag_manifest_is_bag_backed,
    build_not_executed_bundle,
    build_not_executed_manifest,
    degrade_to_partial_if_missing,
    evidence_bundle_missing_files,
    evidence_bundle_required_files,
    init_run_directory,
    load_bag_manifest,
    load_runner_profile,
    load_scenario_plan,
    maturity_report_to_dict,
    render_maturity_markdown,
    runner_profile_from_dict,
    runner_profile_schema,
    runner_profile_to_dict,
    runner_supports_live_execution,
    scenario_plan_from_dict,
    scenario_plan_to_dict,
    validate_bag_manifest,
    validate_runner_profile,
    validate_scenario_plan,
    write_bag_manifest,
    write_evidence_bundle,
    write_maturity_json,
    write_maturity_markdown,
    write_runner_profile,
    write_runner_profile_schema,
)
from app.verification.requirements import (
    RequirementKind,
    RequirementsRegistry,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "live-runtime-evidence.yml"
PLAN_PATH = REPO_ROOT / "live-runtime" / "scenario-plans" / "core-live-qualification.yaml"


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------


def _canonical_runner(**overrides) -> RunnerProfile:
    base = dict(
        runner_id="canonical-runner",
        host_os="ubuntu-24.04",
        ros_distro="jazzy",
        gazebo_version="harmonic",
        colcon_version="0.16.0",
        workspace_path="/home/runner/rover_ws",
        supports_gazebo=True,
        supports_rosbag2=True,
        supports_foxglove_optional=False,
        runner_labels=("self-hosted", "ros-jazzy", "gazebo"),
        last_qualified_at="2026-05-12T00:00:00+00:00",
        qualification_status="qualified",
        known_limitations=(),
    )
    base.update(overrides)
    return RunnerProfile(**base)


def _canonical_bag_manifest(*, status: str = BAG_STATUS_BAG_BACKED, **overrides) -> BagManifest:
    base = dict(
        run_id="run-1",
        scenario_id="nominal_runtime_launch",
        bag_status=status,
        bag_format="mcap",
        bag_paths=("bags/run-1.mcap",) if status == BAG_STATUS_BAG_BACKED else (),
        metadata_yaml_path="bags/metadata.yaml" if status == BAG_STATUS_BAG_BACKED else "",
        topic_inventory=("/safety/state", "/cmd_vel"),
        message_counts={"/safety/state": 100, "/cmd_vel": 100},
        start_time="2026-05-12T00:00:00+00:00",
        end_time="2026-05-12T00:00:30+00:00",
        duration_seconds=30.0,
        missing_required_topics=(),
        validation_status="passed",
        known_limitations=(),
        not_executed_reason="" if status != BAG_STATUS_NOT_EXECUTED else "no jazzy host",
    )
    base.update(overrides)
    return BagManifest(**base)


def _make_real_bundle(tmp: Path, *, run_id: str = "run-1") -> Path:
    """Build a bundle that LOOKS bag_backed and has real bag files on disk."""

    bundle = init_run_directory(tmp, run_id)
    # Create a real (zero-byte) bag file + metadata yaml to satisfy
    # the bag_backed honesty check.
    (bundle / "bags" / "run-1.mcap").write_bytes(b"")
    (bundle / "bags" / "metadata.yaml").write_text(
        "rosbag2_bagfile_information: {}\n", encoding="utf-8"
    )
    summary = LiveRunSummary(
        run_id=run_id,
        runner_id="canonical-runner",
        plan_id="core-live-qualification",
        scenario_ids=("nominal_runtime_launch",),
        started_at="2026-05-12T00:00:00+00:00",
        finished_at="2026-05-12T00:00:30+00:00",
        status=LIVE_RUN_STATUS_PASSED,
        bag_status=BAG_STATUS_BAG_BACKED,
    )
    write_evidence_bundle(
        bundle_dir=bundle,
        run_id=run_id,
        plan_id="core-live-qualification",
        runner_profile=_canonical_runner(),
        summary=summary,
        bag_manifest=_canonical_bag_manifest(),
        events_jsonl='{"event":"safety.state_entered"}\n',
    )
    return bundle


# ----------------------------------------------------------------------
# requirement registry coverage
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "req_id",
    ["REQ-LIVE-001", "REQ-LIVE-002", "REQ-LIVE-003", "REQ-LIVE-004", "REQ-LIVE-005"],
)
def test_requirement_registered(req_id: str):
    registry = RequirementsRegistry()
    assert req_id in registry
    req = registry.get(req_id)
    assert req.kind == RequirementKind.LIVE
    assert req.test_refs, f"{req_id} must list test bindings"


def test_requirement_kind_live_exists():
    assert RequirementKind.LIVE.value == "live"


# ----------------------------------------------------------------------
# runner profile
# ----------------------------------------------------------------------


def test_runner_profile_schema_shape():
    schema = runner_profile_schema()
    assert schema["additionalProperties"] is False
    for f in [
        "runner_id",
        "host_os",
        "ros_distro",
        "gazebo_version",
        "colcon_version",
        "workspace_path",
        "supports_gazebo",
        "supports_rosbag2",
        "supports_foxglove_optional",
    ]:
        assert f in schema["properties"]


def test_runner_profile_load_and_validate(tmp_path: Path):
    prof = _canonical_runner()
    out = tmp_path / "p.json"
    write_runner_profile(prof, out)
    loaded = load_runner_profile(out)
    assert loaded == prof
    assert validate_runner_profile(loaded) == ()
    assert runner_supports_live_execution(loaded) is True


def test_runner_profile_missing_required_fields():
    bad = runner_profile_from_dict({"runner_id": ""})
    warnings = validate_runner_profile(bad)
    assert any("runner_id" in w for w in warnings)
    assert any("rosbag2" in w for w in warnings)
    assert any("Gazebo" in w for w in warnings)
    assert runner_supports_live_execution(bad) is False


def test_runner_profile_none_validation():
    assert validate_runner_profile(None) == ("runner profile missing or unreadable",)
    assert runner_supports_live_execution(None) is False


def test_runner_profile_round_trip_to_dict():
    prof = _canonical_runner(known_limitations=("a", "b"))
    payload = runner_profile_to_dict(prof)
    rebuilt = runner_profile_from_dict(payload)
    assert rebuilt == prof


def test_runner_profile_schema_writer(tmp_path: Path):
    out = tmp_path / "schema.json"
    write_runner_profile_schema(out)
    parsed = json.loads(out.read_text(encoding="utf-8"))
    assert parsed["title"] == "Live runner profile"


# ----------------------------------------------------------------------
# scenario plan
# ----------------------------------------------------------------------


def test_scenario_plan_loads_canonical_yaml():
    plan = load_scenario_plan(PLAN_PATH)
    assert plan is not None, "core-live-qualification.yaml must parse"
    assert plan.plan_id == "core-live-qualification"
    ids = [e.scenario_id for e in plan.entries]
    for required in [
        "nominal_runtime_launch",
        "authorized_motion_path",
        "safe_stop_command_zeroing",
        "stale_lidar_restricted_mode",
        "command_timeout_safe_stop",
        "estop_latched_manual_reset_required",
    ]:
        assert required in ids


def test_scenario_plan_validate_canonical():
    plan = load_scenario_plan(PLAN_PATH)
    warnings = validate_scenario_plan(plan)
    # canonical plan must be free of warnings
    assert warnings == ()


def test_scenario_plan_validate_missing_fields():
    plan = scenario_plan_from_dict(
        {
            "plan_id": "p1",
            "scenarios": [
                {"scenario_id": "", "purpose": "x", "launch_file": "y"},
            ],
        }
    )
    warnings = validate_scenario_plan(plan)
    assert warnings  # some must be reported


def test_scenario_plan_validate_none():
    assert validate_scenario_plan(None) == (
        "scenario plan missing or unparseable",
    )


def test_scenario_plan_to_dict_round_trip():
    plan = load_scenario_plan(PLAN_PATH)
    payload = scenario_plan_to_dict(plan)
    rebuilt = scenario_plan_from_dict(payload)
    assert rebuilt == plan


def test_scenario_plan_loads_with_pyyaml_or_fallback():
    """Ensure the scenario plan parses regardless of pyyaml availability."""

    text = PLAN_PATH.read_text(encoding="utf-8")
    # pyyaml route
    import yaml  # type: ignore[import-not-found]

    payload = yaml.safe_load(text)
    plan_a = scenario_plan_from_dict(payload)
    # fallback route via the scenario_plan internal parser
    from app.live_runtime.scenario_plan import _fallback_parse  # type: ignore[attr-defined]

    payload2 = _fallback_parse(text)
    plan_b = scenario_plan_from_dict(payload2)
    # Plan ids match
    assert plan_a.plan_id == plan_b.plan_id == "core-live-qualification"
    assert {e.scenario_id for e in plan_a.entries} == {
        e.scenario_id for e in plan_b.entries
    }


# ----------------------------------------------------------------------
# bag manifest
# ----------------------------------------------------------------------


def test_bag_manifest_required_fields(tmp_path: Path):
    manifest = _canonical_bag_manifest()
    out = tmp_path / "bag-manifest.json"
    write_bag_manifest(manifest, out)
    loaded = load_bag_manifest(out)
    assert loaded == manifest


def test_bag_manifest_not_executed_reason_required():
    # Construct directly to bypass the default-reason fall-back.
    bad = BagManifest(
        run_id="r",
        scenario_id="s",
        bag_status=BAG_STATUS_NOT_EXECUTED,
        bag_format="",
        bag_paths=(),
        metadata_yaml_path="",
        topic_inventory=(),
        message_counts={},
        start_time="",
        end_time="",
        duration_seconds=0.0,
        missing_required_topics=(),
        validation_status="",
        not_executed_reason="",
    )
    warnings = validate_bag_manifest(bad)
    assert any("not_executed_reason" in w for w in warnings)
    # Helper always supplies a default reason so it never warns.
    helper = build_not_executed_manifest(run_id="r", scenario_id="s", reason="")
    assert helper.not_executed_reason
    assert validate_bag_manifest(helper) == ()


def test_bag_backed_requires_real_artefacts(tmp_path: Path):
    # Manifest claims bag_backed but no files exist on disk.
    manifest = _canonical_bag_manifest()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    write_bag_manifest(manifest, bundle / "bag-manifest.json")
    warnings = validate_bag_manifest(manifest, bundle_root=bundle)
    assert any("bag path missing" in w for w in warnings)


def test_static_fixture_cannot_be_marked_bag_backed():
    """A bag_backed manifest with no bag paths is invalid."""

    manifest = _canonical_bag_manifest(bag_paths=())
    warnings = validate_bag_manifest(manifest)
    assert any("at least one bag path" in w for w in warnings)
    assert bag_manifest_is_bag_backed(manifest) is False


def test_validator_fails_when_manifest_missing(tmp_path: Path):
    warnings = validate_bag_manifest(None)
    assert warnings == ("bag manifest missing or unparseable",)


def test_bag_manifest_unknown_status_rejected():
    manifest = _canonical_bag_manifest(bag_status="bogus")
    warnings = validate_bag_manifest(manifest)
    assert any("not in" in w for w in warnings)


def test_bag_manifest_bag_backed_passes_with_real_files(tmp_path: Path):
    bundle = _make_real_bundle(tmp_path)
    manifest = load_bag_manifest(bundle / "bag-manifest.json")
    warnings = validate_bag_manifest(manifest, bundle_root=bundle)
    assert warnings == ()
    assert bag_manifest_is_bag_backed(manifest) is True


def test_bag_manifest_required_topics_check(tmp_path: Path):
    bundle = _make_real_bundle(tmp_path)
    manifest = load_bag_manifest(bundle / "bag-manifest.json")
    warnings = validate_bag_manifest(
        manifest, bundle_root=bundle, required_topics=("/missing/topic",)
    )
    assert any("required topic missing" in w for w in warnings)


def test_degrade_to_partial_if_missing(tmp_path: Path):
    bundle = _make_real_bundle(tmp_path)
    manifest = load_bag_manifest(bundle / "bag-manifest.json")
    degraded = degrade_to_partial_if_missing(manifest, ("/extra",))
    assert degraded.bag_status == BAG_STATUS_PARTIAL
    assert "/extra" in degraded.missing_required_topics


def test_missing_bag_with_paths_is_invalid():
    manifest = _canonical_bag_manifest(
        bag_status=BAG_STATUS_MISSING_BAG, bag_paths=("bags/x.mcap",)
    )
    warnings = validate_bag_manifest(manifest)
    assert any("inconsistent" in w for w in warnings)


# ----------------------------------------------------------------------
# evidence capture
# ----------------------------------------------------------------------


def test_evidence_capture_aborts_without_ros(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ROS_DISTRO", raising=False)
    from app.live_runtime.evidence_capture import detect_environment_block_reason

    reason = detect_environment_block_reason()
    assert reason and "jazzy" in reason.lower()


def test_evidence_capture_writes_required_files(tmp_path: Path):
    bundle = _make_real_bundle(tmp_path)
    missing = evidence_bundle_missing_files(bundle)
    assert missing == ()
    present = evidence_bundle_required_files(bundle)
    assert set(present) == set(REQUIRED_EVIDENCE_FILES)


def test_not_executed_bundle_layout(tmp_path: Path):
    bundle = init_run_directory(tmp_path, "ne-1")
    build_not_executed_bundle(
        bundle_dir=bundle,
        run_id="ne-1",
        plan_id="core-live-qualification",
        runner_id="template-no-runner",
        runner_profile=None,
        scenario_ids=("nominal_runtime_launch",),
        reason="no jazzy host",
        started_at="2026-05-12T00:00:00+00:00",
        finished_at="2026-05-12T00:00:00+00:00",
    )
    assert (bundle / "bag-manifest.json").exists()
    summary = json.loads((bundle / "live-run-summary.json").read_text("utf-8"))
    assert summary["status"] == LIVE_RUN_STATUS_NOT_EXECUTED
    assert summary["bag_status"] == BAG_STATUS_NOT_EXECUTED
    manifest = load_bag_manifest(bundle / "bag-manifest.json")
    assert manifest.bag_status == BAG_STATUS_NOT_EXECUTED
    assert manifest.not_executed_reason == "no jazzy host"


def test_qualification_summary_md_includes_disclaimer(tmp_path: Path):
    bundle = _make_real_bundle(tmp_path)
    text = (bundle / "qualification-summary.md").read_text("utf-8")
    assert "not safety-certified" in text
    assert "## Scenarios" in text


def test_known_limitations_md_lists_not_executed(tmp_path: Path):
    bundle = init_run_directory(tmp_path, "ne-2")
    build_not_executed_bundle(
        bundle_dir=bundle,
        run_id="ne-2",
        plan_id="core-live-qualification",
        runner_id="template-no-runner",
        runner_profile=None,
        scenario_ids=(),
        reason="no jazzy host",
        started_at="t",
        finished_at="t",
    )
    text = (bundle / "known-limitations.md").read_text("utf-8")
    assert "Live execution did not occur" in text


# ----------------------------------------------------------------------
# maturity report
# ----------------------------------------------------------------------


def test_maturity_report_counts_match_inputs(tmp_path: Path):
    evidence = tmp_path / "evidence" / "runtime"
    evidence.mkdir(parents=True)
    # one bag-backed bundle
    _make_real_bundle(evidence, run_id="run-bb")
    # one not_executed bundle
    bundle_ne = init_run_directory(evidence, "run-ne")
    build_not_executed_bundle(
        bundle_dir=bundle_ne,
        run_id="run-ne",
        plan_id="core-live-qualification",
        runner_id="x",
        runner_profile=None,
        scenario_ids=("nominal_runtime_launch",),
        reason="no jazzy host",
        started_at="t",
        finished_at="t",
    )
    report = aggregate_maturity(
        evidence_root=evidence,
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert report.runs_total == 2
    assert report.bag_counters.bag_backed == 1
    assert report.bag_counters.not_executed == 1
    assert report.runs_by_status[LIVE_RUN_STATUS_PASSED] == 1
    assert report.runs_by_status[LIVE_RUN_STATUS_NOT_EXECUTED] == 1


def test_maturity_report_renders_disclaimer(tmp_path: Path):
    evidence = tmp_path / "ev"
    evidence.mkdir()
    report = aggregate_maturity(
        evidence_root=evidence, generated_at_utc="2026-05-12T00:00:00+00:00"
    )
    md = render_maturity_markdown(report)
    assert "not safety-certified" in md
    assert "## Bag counters" in md


def test_maturity_writer_round_trip(tmp_path: Path):
    evidence = tmp_path / "ev"
    evidence.mkdir()
    report = aggregate_maturity(
        evidence_root=evidence, generated_at_utc="2026-05-12T00:00:00+00:00"
    )
    json_path = tmp_path / "m.json"
    md_path = tmp_path / "m.md"
    write_maturity_json(report, json_path)
    write_maturity_markdown(report, md_path)
    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text("utf-8"))
    assert payload["disclaimer"] == LIVE_RUNTIME_DISCLAIMER


def test_process_live_runtime_evidence_dry_run_preserves_status(tmp_path: Path):
    """The orchestrator must never alter bag_status downstream."""

    bundle = _make_real_bundle(tmp_path)
    # Import the CLI module's plan_actions function. The CLI imports
    # ``_probe_common`` from ``rover_ws/tools/`` so we add that path
    # to sys.path before loading.
    import importlib.util
    import sys as _sys

    tools_dir = REPO_ROOT / "rover_ws" / "tools"
    if str(tools_dir) not in _sys.path:
        _sys.path.insert(0, str(tools_dir))
    cli_path = tools_dir / "process_live_runtime_evidence.py"
    spec = importlib.util.spec_from_file_location("process_live_evidence_cli", cli_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    plan = mod.plan_actions(bundle)
    assert plan["bag_status"] == BAG_STATUS_BAG_BACKED
    assert plan["preserved_bag_status"] == BAG_STATUS_BAG_BACKED
    # bag-backed bundle qualifies for replay-review and analytics.
    steps = {a["step"]: a for a in plan["actions"]}
    assert steps["replay_review_bundle"]["qualifies"] is True
    assert steps["replay_analytics"]["qualifies"] is True


# ----------------------------------------------------------------------
# workflow honesty
# ----------------------------------------------------------------------


def test_workflow_is_self_hosted_only():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "self-hosted" in text
    assert "ros-jazzy" in text
    assert "gazebo" in text


def test_workflow_does_not_target_github_hosted_runners():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    # Reject any of GitHub's hosted runner labels.
    forbidden_runners = ("ubuntu-latest", "ubuntu-22.04", "ubuntu-24.04",
                         "windows-latest", "macos-latest")
    for label in forbidden_runners:
        assert label not in text, f"workflow must not target {label}"


def test_workflow_uses_workflow_dispatch_only():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "workflow_dispatch" in text
    # Forbid push / pull_request / schedule triggers.
    for forbidden_trigger in ("\n  push:", "\n  pull_request:", "\n  schedule:"):
        assert forbidden_trigger not in text, (
            f"workflow must not declare {forbidden_trigger.strip()}"
        )


def test_workflow_refuses_github_hosted_in_runtime_step():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    # The "Refuse GitHub-hosted runners" guard must exist.
    assert "Refuse GitHub-hosted runners" in text
    assert 'ROS_DISTRO' in text


# ----------------------------------------------------------------------
# documentation honesty
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "doc_path",
    [
        "docs/LIVE_RUNTIME_EVIDENCE_PIPELINE.md",
        "docs/LIVE_BAG_CAPTURE_RUNBOOK.md",
        "docs/LIVE_RUNNER_PROFILE.md",
        "docs/LIVE_RUNTIME_MATURITY_REPORT.md",
    ],
)
def test_doc_includes_disclaimer(doc_path: str):
    text = (REPO_ROOT / doc_path).read_text(encoding="utf-8")
    assert "not safety-certified" in text


def test_runner_profile_template_is_unqualified():
    profile = load_runner_profile(REPO_ROOT / "live-runtime" / "runner-profile.json")
    assert profile is not None
    assert profile.qualification_status in ("unknown", "not_qualified", "partial")
    assert profile.supports_gazebo is False
    assert profile.supports_rosbag2 is False
