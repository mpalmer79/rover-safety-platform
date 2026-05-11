"""Phase 14 live runtime honesty guardrail tests.

Every test in this module must run on a GitHub-hosted runner with
no ROS, no Gazebo, and no rosbag2 available. Tests verify the
classifier, the processor, the runner-profile validator, the
maturity baseline rules, the committed templates, the smoke
scenario plan schema, and the self-hosted workflow declaration.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
import yaml

from app.live_runtime import (
    BagStatus,
    EvidenceMode,
    MaturityStatus,
    QualificationOutcome,
    RunnerStatus,
    assert_baseline_honest,
    inspect_bag_directory,
    load_maturity_baseline,
    load_runner_profile,
    load_scenario_plan,
    new_not_established_baseline,
    process_evidence,
    validate_runner_profile,
    validate_scenario_plan,
)
from app.live_runtime.evidence_processor import write_evidence
from app.live_runtime.maturity_baseline import promote_baseline
from app.live_runtime.runner_profile import new_unqualified_template
from app.verification.acceptance import AcceptanceStatus


REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_RUNTIME_DIR = REPO_ROOT / "live-runtime"
DOCS_DIR = REPO_ROOT / "docs"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "live-runtime-evidence.yml"


# ---- Bag classifier ------------------------------------------------


def _make_bag(tmp_path: Path, *, with_metadata: bool, chunk: str | None) -> Path:
    bag_dir = tmp_path / "bag"
    bag_dir.mkdir()
    if with_metadata:
        (bag_dir / "metadata.yaml").write_text(
            textwrap.dedent(
                """
                rosbag2_bagfile_information:
                  storage_identifier: mcap
                  duration:
                    nanoseconds: 1000000
                  topics_with_message_count:
                    - topic_metadata:
                        name: /clock
                        type: rosgraph_msgs/msg/Clock
                      message_count: 100
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
    if chunk == "mcap":
        (bag_dir / "rosbag2.mcap").write_bytes(b"\x00" * 1024)
    elif chunk == "db3":
        (bag_dir / "rosbag2.db3").write_bytes(b"\x00" * 1024)
    elif chunk == "empty":
        (bag_dir / "rosbag2.mcap").write_bytes(b"")
    return bag_dir


def test_missing_bag_directory_is_missing_bag(tmp_path: Path) -> None:
    manifest = inspect_bag_directory(tmp_path / "no-such-bag")
    assert manifest.status is BagStatus.MISSING_BAG
    assert manifest.metadata_present is False
    assert manifest.chunks == ()


def test_no_bag_argument_is_missing_bag() -> None:
    manifest = inspect_bag_directory(None)
    assert manifest.status is BagStatus.MISSING_BAG
    assert manifest.bag_dir is None


def test_metadata_only_bag_is_partial(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=True, chunk=None)
    manifest = inspect_bag_directory(bag)
    assert manifest.status is BagStatus.PARTIAL
    assert manifest.metadata_present is True
    assert manifest.chunks == ()


def test_chunk_without_metadata_is_partial(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=False, chunk="mcap")
    manifest = inspect_bag_directory(bag)
    assert manifest.status is BagStatus.PARTIAL
    assert manifest.metadata_present is False
    assert "metadata.yaml missing" in manifest.reason


def test_metadata_plus_chunk_is_bag_backed(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=True, chunk="mcap")
    manifest = inspect_bag_directory(bag)
    assert manifest.status is BagStatus.BAG_BACKED
    assert manifest.formats == ("mcap",)


def test_metadata_plus_db3_chunk_is_bag_backed(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=True, chunk="db3")
    manifest = inspect_bag_directory(bag)
    assert manifest.status is BagStatus.BAG_BACKED
    assert manifest.formats == ("db3",)


def test_metadata_plus_zero_byte_chunk_is_partial(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=True, chunk="empty")
    manifest = inspect_bag_directory(bag)
    assert manifest.status is BagStatus.PARTIAL
    assert "no data" in manifest.reason


def test_bag_path_that_is_a_file_is_invalid(tmp_path: Path) -> None:
    f = tmp_path / "not_a_dir"
    f.write_text("nope", encoding="utf-8")
    manifest = inspect_bag_directory(f)
    assert manifest.status is BagStatus.INVALID


# ---- Evidence processor honesty -----------------------------------


def _qualified_runner():
    return new_unqualified_template().__class__(
        runner_id="rover-runner-test",
        runner_status=RunnerStatus.PROVISIONAL,
        qualification_status=QualificationOutcome.PARTIAL,
        labels=("self-hosted", "ros-jazzy", "gazebo"),
        host_os="Ubuntu 24.04 LTS",
        ros_distro="jazzy",
        gazebo_version="harmonic",
        python_version="3.12.3",
        workspace_path="/home/runner/rover_ws",
        bag_format="mcap",
    )


def test_dry_run_is_not_executed_and_not_bag_backed(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=True, chunk="mcap")
    evidence = process_evidence(
        run_id="run-dry",
        runner_profile=_qualified_runner(),
        bag_dir=bag,
        dry_run=True,
    )
    assert evidence.mode is EvidenceMode.DRY_RUN
    assert evidence.status is AcceptanceStatus.NOT_EXECUTED
    assert evidence.bag_manifest.status is BagStatus.NOT_EXECUTED
    assert evidence.is_bag_backed is False


def test_static_check_only_is_not_executed_and_not_bag_backed(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=True, chunk="mcap")
    evidence = process_evidence(
        run_id="run-static",
        runner_profile=_qualified_runner(),
        bag_dir=bag,
        static_only=True,
    )
    assert evidence.mode is EvidenceMode.STATIC_ONLY
    assert evidence.status is AcceptanceStatus.NOT_EXECUTED
    assert evidence.bag_manifest.status is BagStatus.NOT_EXECUTED
    assert evidence.is_bag_backed is False


def test_unqualified_runner_cannot_produce_bag_backed_evidence(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=True, chunk="mcap")
    profile = new_unqualified_template()
    evidence = process_evidence(
        run_id="run-unq",
        runner_profile=profile,
        bag_dir=bag,
    )
    assert evidence.mode is EvidenceMode.NOT_EXECUTED
    assert evidence.is_bag_backed is False


def test_no_runner_profile_yields_not_executed(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=True, chunk="mcap")
    evidence = process_evidence(
        run_id="run-noprof",
        runner_profile=None,
        bag_dir=bag,
    )
    assert evidence.mode is EvidenceMode.NOT_EXECUTED


def test_missing_bag_with_qualified_runner_is_partial(tmp_path: Path) -> None:
    evidence = process_evidence(
        run_id="run-missing",
        runner_profile=_qualified_runner(),
        bag_dir=tmp_path / "no-such-bag",
    )
    assert evidence.mode is EvidenceMode.LIVE_RUNTIME_NO_BAG
    assert evidence.status is AcceptanceStatus.PARTIAL
    assert evidence.bag_manifest.status is BagStatus.MISSING_BAG


def test_partial_bag_cannot_be_bag_backed(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=True, chunk=None)
    evidence = process_evidence(
        run_id="run-partial",
        runner_profile=_qualified_runner(),
        bag_dir=bag,
    )
    assert evidence.mode is EvidenceMode.LIVE_RUNTIME_NO_BAG
    assert evidence.status is AcceptanceStatus.PARTIAL


def test_bag_backed_run_is_passed(tmp_path: Path) -> None:
    bag = _make_bag(tmp_path, with_metadata=True, chunk="mcap")
    evidence = process_evidence(
        run_id="run-good",
        runner_profile=_qualified_runner(),
        bag_dir=bag,
    )
    assert evidence.mode is EvidenceMode.BAG_BACKED
    assert evidence.status is AcceptanceStatus.PASSED
    assert evidence.is_bag_backed is True


def test_dry_run_and_static_only_are_mutually_exclusive(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        process_evidence(
            run_id="bad",
            runner_profile=_qualified_runner(),
            dry_run=True,
            static_only=True,
        )


def test_write_evidence_round_trip(tmp_path: Path) -> None:
    evidence = process_evidence(
        run_id="run-rt",
        runner_profile=_qualified_runner(),
        dry_run=True,
    )
    paths = write_evidence(evidence, tmp_path)
    for label in ("evidence_json", "evidence_md", "bag_manifest_json"):
        assert Path(paths[label]).is_file()
    data = json.loads(Path(paths["evidence_json"]).read_text(encoding="utf-8"))
    assert data["mode"] == EvidenceMode.DRY_RUN.value
    assert data["status"] == "not_executed"


# ---- Runner profile templates -------------------------------------


def test_committed_template_profile_loads_and_is_unqualified() -> None:
    profile = load_runner_profile(
        LIVE_RUNTIME_DIR / "runner-profile.template.json"
    )
    assert profile.runner_status is RunnerStatus.UNQUALIFIED
    assert profile.qualification_status is QualificationOutcome.NOT_EXECUTED
    assert profile.last_bag_backed_run_id is None
    errors = validate_runner_profile(profile)
    assert errors == []


def test_committed_template_profile_cannot_be_qualified_without_evidence() -> None:
    profile = load_runner_profile(
        LIVE_RUNTIME_DIR / "runner-profile.template.json"
    )
    # The template MUST stay unqualified; if someone flips it to
    # qualified without recording a bag-backed run, the validator
    # must reject it.
    cheat = profile.__class__(
        runner_id=profile.runner_id,
        runner_status=RunnerStatus.QUALIFIED,
        qualification_status=QualificationOutcome.PASSED,
        labels=profile.labels,
        host_os=profile.host_os,
        ros_distro=profile.ros_distro,
        gazebo_version=profile.gazebo_version,
        python_version=profile.python_version,
        workspace_path=profile.workspace_path,
        bag_format=profile.bag_format,
        last_qualified_at=None,
        last_qualified_run_id=None,
        last_bag_backed_run_id=None,
    )
    errors = validate_runner_profile(cheat)
    assert any("last_qualified_at" in e for e in errors)
    assert any("last_qualified_run_id" in e for e in errors)
    assert any("bag-backed" in e for e in errors)


def test_committed_example_profile_loads_and_is_provisional() -> None:
    profile = load_runner_profile(
        LIVE_RUNTIME_DIR / "runner-profile.local.example.json"
    )
    assert profile.runner_status is RunnerStatus.PROVISIONAL
    errors = validate_runner_profile(profile)
    assert errors == []


def test_runner_profile_requires_self_hosted_labels() -> None:
    profile = new_unqualified_template()
    bad = profile.__class__(**{**profile.__dict__, "labels": ("self-hosted",)})
    errors = validate_runner_profile(bad)
    assert any("ros-jazzy" in e for e in errors)
    assert any("gazebo" in e for e in errors)


def test_runner_profile_rejects_github_hosted_labels() -> None:
    profile = new_unqualified_template()
    bad = profile.__class__(
        **{
            **profile.__dict__,
            "labels": ("self-hosted", "ros-jazzy", "gazebo", "ubuntu-latest"),
        }
    )
    errors = validate_runner_profile(bad)
    assert any("ubuntu-latest" in e for e in errors)


def test_runner_profile_qualified_requires_bag_backed() -> None:
    profile = new_unqualified_template()
    bad = profile.__class__(
        **{
            **profile.__dict__,
            "runner_status": RunnerStatus.QUALIFIED,
            "qualification_status": QualificationOutcome.PASSED,
            "last_qualified_at": "2026-05-11T00:00:00+00:00",
            "last_qualified_run_id": "run-1",
            "last_bag_backed_run_id": None,
        }
    )
    errors = validate_runner_profile(bad)
    assert any("bag-backed" in e for e in errors)


# ---- Maturity baseline --------------------------------------------


def test_committed_maturity_baseline_template_is_not_established() -> None:
    baseline = load_maturity_baseline(
        LIVE_RUNTIME_DIR / "baselines" / "maturity-baseline.template.json"
    )
    assert baseline.status is MaturityStatus.NOT_ESTABLISHED
    assert baseline.bag_backed_runs == 0
    errors = assert_baseline_honest(baseline, has_bag_backed_evidence=False)
    assert errors == []


def test_baseline_cannot_claim_established_without_bag_backed() -> None:
    baseline = new_not_established_baseline()
    promoted_data = {
        **baseline.as_dict(),
        "status": "established",
        "bag_backed_runs": 1,
        "last_run_id": "run-x",
    }
    from app.live_runtime.maturity_baseline import parse_maturity_baseline

    bad = parse_maturity_baseline(promoted_data)
    errors = assert_baseline_honest(bad, has_bag_backed_evidence=False)
    assert any("no bag-backed evidence" in e for e in errors)


def test_baseline_promotion_requires_bag_backed_input() -> None:
    previous = new_not_established_baseline()
    promoted = promote_baseline(
        previous,
        run_id="run-y",
        bag_dir="/tmp/bag",
        runner_id="rover-runner-test",
        scenario_plan_id="smoke-live-runtime",
        captured_at="2026-05-11T00:00:00+00:00",
    )
    assert promoted.status is MaturityStatus.ESTABLISHED
    # promote_baseline does NOT validate; the pipeline is the gate.
    # Ensure the audit catches a bogus established record without
    # accompanying bag-backed evidence.
    errors = assert_baseline_honest(promoted, has_bag_backed_evidence=False)
    assert errors  # promotion without evidence is detected by the audit


# ---- Scenario plans -----------------------------------------------


def test_smoke_scenario_plan_loads_and_validates() -> None:
    plan = load_scenario_plan(
        LIVE_RUNTIME_DIR / "scenario-plans" / "smoke-live-runtime.yaml"
    )
    assert plan.smoke is True
    assert plan.expected_evidence_mode == "bag_backed"
    errors = validate_scenario_plan(plan)
    assert errors == []


def test_core_scenario_plan_loads_and_validates() -> None:
    plan = load_scenario_plan(
        LIVE_RUNTIME_DIR / "scenario-plans" / "core-live-qualification.yaml"
    )
    assert plan.smoke is False
    errors = validate_scenario_plan(plan)
    assert errors == []


def test_scenario_plan_requires_bag_topics_for_required_topics() -> None:
    plan = load_scenario_plan(
        LIVE_RUNTIME_DIR / "scenario-plans" / "smoke-live-runtime.yaml"
    )
    bad = plan.__class__(
        **{
            **plan.__dict__,
            "required_topics": plan.required_topics + ("/missing/topic",),
        }
    )
    errors = validate_scenario_plan(bad)
    assert any("/missing/topic" in e for e in errors)


def test_scenario_plan_rejects_zero_duration() -> None:
    plan = load_scenario_plan(
        LIVE_RUNTIME_DIR / "scenario-plans" / "smoke-live-runtime.yaml"
    )
    bad = plan.__class__(**{**plan.__dict__, "duration_seconds": 0})
    errors = validate_scenario_plan(bad)
    assert any("> 0" in e for e in errors)


# ---- Workflow hardening --------------------------------------------


def test_self_hosted_workflow_exists() -> None:
    assert WORKFLOW_PATH.is_file()


def test_self_hosted_workflow_only_runs_on_self_hosted() -> None:
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    job = data["jobs"]["live-runtime-evidence"]
    runs_on = job["runs-on"]
    assert isinstance(runs_on, list)
    assert "self-hosted" in runs_on
    assert "ros-jazzy" in runs_on
    assert "gazebo" in runs_on
    forbidden = {"ubuntu-latest", "ubuntu-24.04", "windows-latest", "macos-latest"}
    assert not (set(runs_on) & forbidden), runs_on


def test_self_hosted_workflow_is_workflow_dispatch_only() -> None:
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    # YAML "on:" is parsed by PyYAML as the boolean True key.
    triggers = data.get("on") or data.get(True)
    assert triggers is not None
    assert isinstance(triggers, dict)
    assert "workflow_dispatch" in triggers
    assert set(triggers.keys()) == {"workflow_dispatch"}


def test_self_hosted_workflow_uploads_evidence() -> None:
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    steps = data["jobs"]["live-runtime-evidence"]["steps"]
    upload_steps = [s for s in steps if "upload-artifact" in str(s.get("uses", ""))]
    assert upload_steps, "workflow must upload at least one artifact"


# ---- Documentation honesty -----------------------------------------


@pytest.mark.parametrize(
    "doc",
    [
        "SELF_HOSTED_JAZZY_RUNNER_SETUP.md",
        "LIVE_RUNTIME_EVIDENCE_PIPELINE.md",
        "LIVE_BAG_CAPTURE_RUNBOOK.md",
        "LIVE_RUNNER_PROFILE.md",
        "LIVE_RUNTIME_MATURITY_REPORT.md",
    ],
)
def test_live_runtime_doc_includes_not_safety_certified_disclaimer(doc: str) -> None:
    text = (DOCS_DIR / doc).read_text(encoding="utf-8")
    assert "not safety-certified" in text.lower()


def test_live_runtime_maturity_report_states_not_established() -> None:
    text = (DOCS_DIR / "LIVE_RUNTIME_MATURITY_REPORT.md").read_text(
        encoding="utf-8"
    )
    assert "not_established" in text


# ---- Process_live_runtime_evidence behaviour ----------------------


def test_process_preserves_missing_bag_for_unqualified_runner(tmp_path: Path) -> None:
    """A missing bag plus an unqualified runner stays not_executed."""

    profile = new_unqualified_template()
    evidence = process_evidence(
        run_id="run-z",
        runner_profile=profile,
        bag_dir=tmp_path / "no-bag",
    )
    assert evidence.mode is EvidenceMode.NOT_EXECUTED
    assert evidence.bag_manifest.status is BagStatus.MISSING_BAG


def test_process_preserves_missing_bag_for_qualified_runner(tmp_path: Path) -> None:
    """A qualified runner without a bag is partial, not bag_backed."""

    evidence = process_evidence(
        run_id="run-z2",
        runner_profile=_qualified_runner(),
        bag_dir=tmp_path / "no-bag",
    )
    assert evidence.mode is EvidenceMode.LIVE_RUNTIME_NO_BAG
    assert evidence.is_bag_backed is False
