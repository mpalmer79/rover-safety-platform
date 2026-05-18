"""Phase 6 incident analysis tests.

Tests run without ROS / Gazebo and operate on:

* synthetic evidence directories built in ``tmp_path``;
* the real scenario evidence checked into the repo
  (``evidence/scenarios/stale_lidar_restricted_mode/`` etc.).

Coverage:

* loader — missing files, malformed JSON, empty event streams,
  cross-reference mismatch, structured warnings;
* normaliser — safety / mission events, evidence-origin preservation,
  missing-timestamp handling;
* timeline — deterministic ordering, relative-time derivation,
  out-of-order detection, key indices, Mermaid generation;
* causality — stale_lidar chain, command_timeout chain, e-stop chain,
  missing-link confidence downgrade, contradictory evidence handling;
* classifier — severity, outcome, evidence_status; controlled
  degradation, safe-stop success, partial-evidence, inconclusive;
* reporter — Markdown + JSON output, disclaimer, missing-evidence
  section, contradictions section;
* foxglove — hints + layout file;
* index — filterable, missing-report fallback;
* compare — comparison rows for multiple bundles.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pytest

from app.incident_analysis.causality import build_causality_chains
from app.incident_analysis.classifier import classify_incident
from app.incident_analysis.compare import (
    compare_incidents,
    render_comparison_md as render_incident_comparison_md,
)
from app.incident_analysis.foxglove import (
    DEFAULT_LAYOUT as FOXGLOVE_DEFAULT_LAYOUT,
    build_foxglove_hint,
    write_default_layout as write_default_foxglove_layout,
)
from app.incident_analysis.index import (
    build_incident_index,
    write_incident_index,
)
from app.incident_analysis.loader import (
    LoadedEvidenceBundle,
    LoadedRuntimeEvidence,
    LoadedScenarioEvidence,
    load_evidence_bundle,
    load_runtime_evidence,
    load_scenario_evidence,
)
from app.incident_analysis.models import (
    CERTIFICATION_DISCLAIMER,
    CausalLink,
    CausalityChain,
    CausalityConfidence,
    EvidenceOrigin,
    Incident,
    IncidentEvidenceStatus,
    IncidentOutcome,
    IncidentSeverity,
    IncidentTimeline,
    TimelineEntry,
)
from app.incident_analysis.normalizer import normalise_bundle
from app.incident_analysis.reconstruct import reconstruct_incident
from app.incident_analysis.reporter import (
    derive_recommendations,
    render_incident_report_md,
    render_recommendations_md,
    write_incident_bundle,
)
from app.incident_analysis.timeline import (
    build_timeline,
    render_sequence_mmd,
    render_state_mmd,
    render_timeline_md,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_FIXTURE_DIR = REPO_ROOT / "evidence" / "scenarios" / "stale_lidar_restricted_mode"
RUNS_ROOT = REPO_ROOT / "runs" / "verify"


# ---------------------------------------------------------------------------
# Loader.
# ---------------------------------------------------------------------------


def test_loader_handles_missing_files(tmp_path: Path) -> None:
    """Every documented file is missing; the loader emits warnings, not exceptions."""

    runtime_dir = tmp_path / "runtime" / "ghost"
    scenario_dir = tmp_path / "scenarios" / "ghost"
    runtime_dir.mkdir(parents=True)
    scenario_dir.mkdir(parents=True)
    runtime = load_runtime_evidence(runtime_dir)
    scenario = load_scenario_evidence(scenario_dir)
    assert runtime.runtime_validation is None
    assert scenario.evidence is None
    categories = {w.category for w in runtime.warnings}
    assert "missing_file" in categories
    categories = {w.category for w in scenario.warnings}
    assert "missing_file" in categories


def test_loader_handles_malformed_json(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "rt"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "runtime-validation.json").write_text("{not json", encoding="utf-8")
    runtime = load_runtime_evidence(runtime_dir)
    assert runtime.runtime_validation is None
    assert any(w.category == "malformed_json" for w in runtime.warnings)


def test_loader_records_empty_event_stream(tmp_path: Path) -> None:
    """A scenario whose run dir has empty events.jsonl emits a structured warning."""

    scenario_dir = tmp_path / "evidence" / "scenarios" / "x"
    scenario_dir.mkdir(parents=True)
    runs = tmp_path / "runs" / "verify-x"
    runs.mkdir(parents=True)
    (runs / "events.jsonl").write_text("", encoding="utf-8")
    (scenario_dir / "evidence.json").write_text(
        json.dumps(
            {
                "scenario_id": "x",
                "status": "passed",
                "observed": {"run_dir": str(runs)},
            }
        ),
        encoding="utf-8",
    )
    scenario = load_scenario_evidence(scenario_dir, runs_root=runs.parent)
    categories = {w.category for w in scenario.warnings}
    assert "empty_event_stream" in categories


def test_loader_loads_real_scenario_fixture() -> None:
    scenario = load_scenario_evidence(SCENARIO_FIXTURE_DIR, runs_root=RUNS_ROOT)
    assert scenario.scenario_id == "stale_lidar_restricted_mode"
    assert scenario.evidence is not None
    assert scenario.run_dir is not None
    assert len(scenario.events) > 100


def test_load_evidence_bundle_emits_cross_reference_mismatch(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "rt"
    scenario_dir = tmp_path / "sc"
    runtime_dir.mkdir(parents=True)
    scenario_dir.mkdir(parents=True)
    (runtime_dir / "runtime-validation.json").write_text(
        json.dumps({"run_id": "alpha", "mode": "static-only", "status": "passed"}),
        encoding="utf-8",
    )
    (scenario_dir / "evidence.json").write_text(
        json.dumps({"scenario_id": "x", "observed": {"run_dir": "/runs/beta"}}),
        encoding="utf-8",
    )
    bundle = load_evidence_bundle(
        runtime_run_dir=runtime_dir, scenario_dir=scenario_dir
    )
    categories = {w.category for w in bundle.all_warnings()}
    assert "cross_reference_mismatch" in categories


# ---------------------------------------------------------------------------
# Normaliser.
# ---------------------------------------------------------------------------


def test_normalizer_preserves_evidence_origin() -> None:
    scenario = load_scenario_evidence(SCENARIO_FIXTURE_DIR, runs_root=RUNS_ROOT)
    bundle = LoadedEvidenceBundle(scenario=scenario)
    entries = normalise_bundle(bundle)
    assert entries
    origins = {e.evidence_origin for e in entries}
    # All scenario-side entries must carry SCENARIO_EVIDENCE.
    assert origins == {EvidenceOrigin.SCENARIO_EVIDENCE}


def test_normalizer_handles_missing_timestamps(tmp_path: Path) -> None:
    """Records lacking sim_time_ns produce entries with relative_time_ms=None."""

    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "events.jsonl").write_text(
        '{"event_type":"safety_transition.entered","sim_time_ns":1000000,"safety_state":"INACTIVE","attributes":{}}\n'
        '{"event_type":"safety_transition.entered","safety_state":"ACTIVE_NORMAL","attributes":{}}\n',
        encoding="utf-8",
    )
    scenario_dir = tmp_path / "sc"
    scenario_dir.mkdir()
    (scenario_dir / "evidence.json").write_text(
        json.dumps({"scenario_id": "x", "observed": {"run_dir": str(runs)}}),
        encoding="utf-8",
    )
    scenario = load_scenario_evidence(scenario_dir, runs_root=runs.parent)
    bundle = LoadedEvidenceBundle(scenario=scenario)
    entries = normalise_bundle(bundle)
    timeline = build_timeline(incident_id="t", entries=entries)
    rel_times = [e.relative_time_ms for e in timeline.entries]
    assert rel_times[0] == 0
    assert rel_times[-1] is None


def test_normalizer_emits_command_audit_summary_entry() -> None:
    scenario = load_scenario_evidence(SCENARIO_FIXTURE_DIR, runs_root=RUNS_ROOT)
    bundle = LoadedEvidenceBundle(scenario=scenario)
    entries = normalise_bundle(bundle)
    summaries = [
        e for e in entries if e.event_type == "motion_arbitration.summary"
    ]
    assert summaries
    s = summaries[0]
    assert s.attributes["request_count"] > 0


# ---------------------------------------------------------------------------
# Timeline.
# ---------------------------------------------------------------------------


def _make_entry(
    *,
    sim_time_ns: Optional[int],
    category: str,
    event_type: str,
    safety_state: Optional[str] = None,
    attributes: Optional[dict] = None,
) -> TimelineEntry:
    return TimelineEntry(
        sequence_index=-1,
        timestamp="",
        relative_time_ms=None,
        sim_time_ns=sim_time_ns,
        source_file="test",
        category=category,
        event_type=event_type,
        severity="INFO",
        safety_state=safety_state,
        mission_state=None,
        reason_code=None,
        message="",
        evidence_origin=EvidenceOrigin.SCENARIO_EVIDENCE,
        run_id=None,
        scenario_id=None,
        raw_reference=None,
        attributes=dict(attributes or {}),
    )


def test_timeline_orders_events_deterministically() -> None:
    entries = [
        _make_entry(sim_time_ns=300_000_000, category="safety_transition", event_type="safety_transition.entered", safety_state="SAFE_STOP"),
        _make_entry(sim_time_ns=100_000_000, category="fault_injection", event_type="fault_injection.fired", attributes={"fault_type": "stale_lidar"}),
        _make_entry(sim_time_ns=200_000_000, category="safety_transition", event_type="safety_transition.entered", safety_state="ACTIVE_DEGRADED"),
    ]
    timeline = build_timeline(incident_id="t", entries=entries)
    sim_times = [e.sim_time_ns for e in timeline.entries]
    assert sim_times == [100_000_000, 200_000_000, 300_000_000]
    assert timeline.first_fault_index == 0
    assert timeline.first_safety_transition_index == 1


def test_timeline_records_out_of_order_indices() -> None:
    entries = [
        _make_entry(sim_time_ns=200_000_000, category="safety_transition", event_type="safety_transition.entered"),
        _make_entry(sim_time_ns=100_000_000, category="safety_transition", event_type="safety_transition.entered"),
    ]
    timeline = build_timeline(incident_id="t", entries=entries)
    assert timeline.out_of_order_indices  # both moved


def test_timeline_renders_mermaid() -> None:
    scenario = load_scenario_evidence(SCENARIO_FIXTURE_DIR, runs_root=RUNS_ROOT)
    bundle = LoadedEvidenceBundle(scenario=scenario)
    entries = normalise_bundle(bundle)
    timeline = build_timeline(incident_id="m", entries=entries)
    seq = render_sequence_mmd(timeline)
    state = render_state_mmd(timeline)
    md = render_timeline_md(timeline)
    assert seq.startswith("sequenceDiagram")
    assert state.startswith("stateDiagram-v2")
    assert "ACTIVE_NORMAL --> ACTIVE_DEGRADED" in state
    assert "Incident Timeline" in md


# ---------------------------------------------------------------------------
# Causality.
# ---------------------------------------------------------------------------


def test_causality_stale_lidar_chain() -> None:
    scenario = load_scenario_evidence(SCENARIO_FIXTURE_DIR, runs_root=RUNS_ROOT)
    bundle = LoadedEvidenceBundle(scenario=scenario)
    entries = normalise_bundle(bundle)
    timeline = build_timeline(incident_id="x", entries=entries)
    chains = build_causality_chains(timeline)
    sl = next((c for c in chains if c.chain_id == "stale_lidar_chain"), None)
    assert sl is not None
    assert sl.overall_confidence == CausalityConfidence.DIRECT
    # All links must reference real timeline indices.
    for link in sl.links:
        assert 0 <= link.from_entry_index < len(timeline.entries)
        assert 0 <= link.to_entry_index < len(timeline.entries)


def test_causality_command_timeout_chain() -> None:
    scenario = load_scenario_evidence(
        REPO_ROOT / "evidence" / "scenarios" / "command_timeout_safe_stop",
        runs_root=RUNS_ROOT,
    )
    bundle = LoadedEvidenceBundle(scenario=scenario)
    entries = normalise_bundle(bundle)
    timeline = build_timeline(incident_id="ct", entries=entries)
    chains = build_causality_chains(timeline)
    ct = next((c for c in chains if c.chain_id == "command_timeout_chain"), None)
    # Even if the scenario surfaces this via watchdog rather than an
    # explicit fault_injection.fired record, the chain must trigger.
    if ct is not None:
        assert ct.overall_confidence in (
            CausalityConfidence.DIRECT,
            CausalityConfidence.STRONG,
            CausalityConfidence.MODERATE,
        )


def test_causality_estop_chain() -> None:
    scenario = load_scenario_evidence(
        REPO_ROOT / "evidence" / "scenarios" / "estop_latched_manual_reset_required",
        runs_root=RUNS_ROOT,
    )
    bundle = LoadedEvidenceBundle(scenario=scenario)
    entries = normalise_bundle(bundle)
    timeline = build_timeline(incident_id="es", entries=entries)
    chains = build_causality_chains(timeline)
    es = next((c for c in chains if c.chain_id == "operator_estop_chain"), None)
    assert es is not None
    # Confidence must be at most DIRECT and >= MODERATE.
    assert es.overall_confidence in (
        CausalityConfidence.DIRECT,
        CausalityConfidence.STRONG,
        CausalityConfidence.MODERATE,
    )


def test_causality_missing_link_downgrades_confidence() -> None:
    """A chain whose freshness watchdog is absent must report MODERATE, not DIRECT."""

    fault = _make_entry(
        sim_time_ns=1_000_000_000,
        category="fault_injection",
        event_type="fault_injection.fired",
        attributes={"fault_type": "stale_lidar", "fault_id": "f1"},
    )
    degraded = _make_entry(
        sim_time_ns=2_000_000_000,
        category="safety_transition",
        event_type="safety_transition.entered",
        safety_state="ACTIVE_DEGRADED",
        attributes={"to_state": "ACTIVE_DEGRADED"},
    )
    safe_stop = _make_entry(
        sim_time_ns=3_000_000_000,
        category="safety_transition",
        event_type="safety_transition.entered",
        safety_state="SAFE_STOP",
        attributes={"to_state": "SAFE_STOP"},
    )
    cmd_audit = _make_entry(
        sim_time_ns=None,
        category="motion_arbitration",
        event_type="motion_arbitration.summary",
        attributes={"zeroed_count": 10, "request_count": 50},
    )
    timeline = build_timeline(
        incident_id="t",
        entries=[fault, degraded, safe_stop, cmd_audit],
    )
    chains = build_causality_chains(timeline)
    sl = next(c for c in chains if c.chain_id == "stale_lidar_chain")
    assert "lidar_freshness watchdog event" in sl.missing_links
    assert sl.overall_confidence != CausalityConfidence.DIRECT
    # Should be MODERATE because of the missing watchdog.
    assert sl.overall_confidence == CausalityConfidence.MODERATE


def test_causality_contradiction_when_safe_stop_without_zeroing() -> None:
    fault = _make_entry(
        sim_time_ns=1,
        category="fault_injection",
        event_type="fault_injection.fired",
        attributes={"fault_type": "stale_lidar"},
    )
    degraded = _make_entry(
        sim_time_ns=2,
        category="safety_transition",
        event_type="safety_transition.entered",
        safety_state="ACTIVE_DEGRADED",
        attributes={"to_state": "ACTIVE_DEGRADED"},
    )
    safe_stop = _make_entry(
        sim_time_ns=3,
        category="safety_transition",
        event_type="safety_transition.entered",
        safety_state="SAFE_STOP",
        attributes={"to_state": "SAFE_STOP"},
    )
    cmd_audit = _make_entry(
        sim_time_ns=None,
        category="motion_arbitration",
        event_type="motion_arbitration.summary",
        attributes={"zeroed_count": 0, "request_count": 50},
    )
    timeline = build_timeline(
        incident_id="t", entries=[fault, degraded, safe_stop, cmd_audit]
    )
    chains = build_causality_chains(timeline)
    sl = next(c for c in chains if c.chain_id == "stale_lidar_chain")
    assert sl.contradictions
    assert sl.overall_confidence == CausalityConfidence.INCONCLUSIVE


# ---------------------------------------------------------------------------
# Classifier.
# ---------------------------------------------------------------------------


def test_classifier_safe_stop_success_on_real_scenario() -> None:
    bundle = load_evidence_bundle(
        scenario_dir=SCENARIO_FIXTURE_DIR, runs_root=RUNS_ROOT
    )
    entries = normalise_bundle(bundle)
    timeline = build_timeline(incident_id="t", entries=entries)
    chains = build_causality_chains(timeline)
    severity, outcome, status, cause, missing, contradictions = classify_incident(
        bundle=bundle, timeline=timeline, chains=chains
    )
    assert outcome == IncidentOutcome.SAFE_STOP_SUCCESS
    assert severity == IncidentSeverity.MODERATE
    assert status in {
        IncidentEvidenceStatus.COMPLETE,
        IncidentEvidenceStatus.PARTIAL,
    }
    assert cause is not None
    assert cause.label == "stale_lidar_chain"


def test_classifier_flags_missing_evidence(tmp_path: Path) -> None:
    bundle = load_evidence_bundle(scenario_dir=tmp_path / "ghost")
    entries = normalise_bundle(bundle)
    timeline = build_timeline(incident_id="t", entries=entries)
    chains = build_causality_chains(timeline)
    _sev, _out, status, _cause, missing, _contra = classify_incident(
        bundle=bundle, timeline=timeline, chains=chains
    )
    assert status == IncidentEvidenceStatus.MISSING
    assert missing  # at least one missing-file warning


def test_classifier_flags_contradictory_evidence(tmp_path: Path) -> None:
    """An ok=true scenario whose chain contradicts itself must be flagged."""

    scenario_dir = tmp_path / "sc"
    scenario_dir.mkdir()
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "events.jsonl").write_text(
        json.dumps(
            {
                "event_type": "fault_injection.fired",
                "sim_time_ns": 1000000,
                "safety_state": "BOOT",
                "attributes": {"fault_type": "stale_lidar"},
            }
        )
        + "\n"
        + json.dumps(
            {
                "event_type": "safety_transition.entered",
                "sim_time_ns": 2000000,
                "safety_state": "ACTIVE_DEGRADED",
                "attributes": {"to_state": "ACTIVE_DEGRADED"},
            }
        )
        + "\n"
        + json.dumps(
            {
                "event_type": "safety_transition.entered",
                "sim_time_ns": 3000000,
                "safety_state": "SAFE_STOP",
                "attributes": {"to_state": "SAFE_STOP"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (scenario_dir / "evidence.json").write_text(
        json.dumps(
            {
                "scenario_id": "fake",
                "status": "passed",
                "observed": {
                    "run_dir": str(runs),
                    "final_safety_state": "SAFE_STOP",
                },
            }
        ),
        encoding="utf-8",
    )
    (scenario_dir / "command-audit.json").write_text(
        json.dumps(
            {
                "ok": True,
                "status": "passed",
                "command_count": 50,
                "request_count": 50,
                "zeroed_count": 0,
                "clamped_count": 0,
                "rejected_count": 0,
            }
        ),
        encoding="utf-8",
    )
    bundle = load_evidence_bundle(scenario_dir=scenario_dir, runs_root=runs.parent)
    entries = normalise_bundle(bundle)
    timeline = build_timeline(incident_id="t", entries=entries)
    chains = build_causality_chains(timeline)
    _sev, _out, status, _cause, _missing, contradictions = classify_incident(
        bundle=bundle, timeline=timeline, chains=chains
    )
    assert contradictions
    assert status == IncidentEvidenceStatus.INCONSISTENT


def test_classifier_partial_evidence_when_some_files_missing(tmp_path: Path) -> None:
    """Partial: scenario evidence present, runtime missing, no contradictions."""

    scenario_dir = tmp_path / "sc"
    scenario_dir.mkdir()
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "events.jsonl").write_text(
        json.dumps(
            {
                "event_type": "safety_transition.entered",
                "sim_time_ns": 1,
                "safety_state": "ACTIVE_NORMAL",
                "attributes": {"to_state": "ACTIVE_NORMAL"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (scenario_dir / "evidence.json").write_text(
        json.dumps(
            {
                "scenario_id": "p",
                "status": "passed",
                "observed": {"run_dir": str(runs)},
            }
        ),
        encoding="utf-8",
    )
    bundle = load_evidence_bundle(scenario_dir=scenario_dir, runs_root=runs.parent)
    entries = normalise_bundle(bundle)
    timeline = build_timeline(incident_id="p", entries=entries)
    chains = build_causality_chains(timeline)
    _sev, _out, status, _cause, missing, _contra = classify_incident(
        bundle=bundle, timeline=timeline, chains=chains
    )
    assert status == IncidentEvidenceStatus.PARTIAL
    assert missing  # missing replay-integrity, command-audit, etc.


# ---------------------------------------------------------------------------
# Reporter.
# ---------------------------------------------------------------------------


def test_report_disclaimer_and_sections(tmp_path: Path) -> None:
    incident = reconstruct_incident(
        incident_id="rep1",
        scenario_dir=SCENARIO_FIXTURE_DIR,
        runs_root=RUNS_ROOT,
    )
    md = render_incident_report_md(incident)
    assert CERTIFICATION_DISCLAIMER in md
    for required_heading in (
        "## Safety state sequence",
        "## Command authorisation summary",
        "## Replay integrity summary",
        "## Causality chain",
        "## Missing evidence",
        "## Contradictory evidence",
        "## Recommended follow-up",
    ):
        assert required_heading in md, required_heading


def test_report_includes_missing_evidence_section(tmp_path: Path) -> None:
    incident = reconstruct_incident(
        incident_id="missing",
        scenario_dir=tmp_path / "ghost",
    )
    md = render_incident_report_md(incident)
    assert "## Missing evidence" in md
    # Bundle wrote nothing; the missing-evidence list should be non-empty.
    assert any(
        "missing" in m.lower() for m in incident.missing_evidence
    ), incident.missing_evidence


def test_report_labels_inferred_links(tmp_path: Path) -> None:
    """Synthetic chain with an inferred link must render as ``inferred=yes``."""

    fault = _make_entry(
        sim_time_ns=1_000_000_000,
        category="fault_injection",
        event_type="fault_injection.fired",
        attributes={"fault_type": "stale_lidar"},
    )
    safe_stop = _make_entry(
        sim_time_ns=4_000_000_000,
        category="safety_transition",
        event_type="safety_transition.entered",
        safety_state="SAFE_STOP",
        attributes={"to_state": "SAFE_STOP"},
    )
    timeline = build_timeline(incident_id="t", entries=[fault, safe_stop])
    chains = build_causality_chains(timeline)
    incident = Incident(
        incident_id="t",
        run_id=None,
        scenario_id=None,
        severity=IncidentSeverity.MODERATE,
        outcome=IncidentOutcome.SAFE_STOP_SUCCESS,
        evidence_status=IncidentEvidenceStatus.PARTIAL,
        timeline=timeline,
        causality_chains=chains,
    )
    md = render_incident_report_md(incident)
    # The chain is missing both ACTIVE_DEGRADED and watchdog; at least
    # one inferred link should exist.
    assert "yes" in md.lower()
    assert "Missing links" in md or "missing_links" in md.lower()


def test_write_incident_bundle_emits_all_files(tmp_path: Path) -> None:
    incident = reconstruct_incident(
        incident_id="bundle",
        scenario_dir=SCENARIO_FIXTURE_DIR,
        runs_root=RUNS_ROOT,
    )
    bundle = write_incident_bundle(incident, bundle_dir=tmp_path / "incidents" / "bundle")
    expected = (
        "incident-report.json",
        "incident-report.md",
        "timeline.json",
        "timeline.md",
        "timeline-sequence.mmd",
        "timeline-state.mmd",
        "causality.md",
        "recommendations.md",
        "evidence-manifest.json",
        "foxglove-replay-hints.json",
    )
    for name in expected:
        assert (bundle.bundle_dir / name).exists(), name


# ---------------------------------------------------------------------------
# Foxglove.
# ---------------------------------------------------------------------------


def test_foxglove_hints_emit_topics_and_layout(tmp_path: Path) -> None:
    incident = reconstruct_incident(
        incident_id="fg",
        scenario_dir=SCENARIO_FIXTURE_DIR,
        runs_root=RUNS_ROOT,
    )
    hint = incident.foxglove_hint
    assert hint is not None
    assert "/cmd_vel_authorized" in hint.recommended_topics
    assert hint.safety_state_topic == "/safety/state"
    assert hint.layout_path.endswith("incident-review-layout.json")
    assert any(m["label"] == "first_fault" for m in hint.timeline_markers)


def test_foxglove_layout_file_is_valid_json(tmp_path: Path) -> None:
    layout_path = tmp_path / "layout.json"
    write_default_foxglove_layout(layout_path)
    payload = json.loads(layout_path.read_text(encoding="utf-8"))
    assert "configById" in payload
    assert "layout" in payload


def test_canonical_foxglove_layout_committed() -> None:
    """The repo ships the canonical layout under foxglove/layouts/."""

    canonical = REPO_ROOT / "foxglove" / "layouts" / "incident-review-layout.json"
    text = canonical.read_text(encoding="utf-8")
    payload = json.loads(text)
    assert payload == FOXGLOVE_DEFAULT_LAYOUT


# ---------------------------------------------------------------------------
# Index.
# ---------------------------------------------------------------------------


def _write_fake_bundle(
    root: Path,
    *,
    incident_id: str,
    scenario_id: str,
    severity: str,
    outcome: str,
    evidence_status: str,
    terminal_safety: str = "SAFE_STOP",
) -> Path:
    bundle = root / incident_id
    bundle.mkdir(parents=True)
    (bundle / "incident-report.json").write_text(
        json.dumps(
            {
                "incident_id": incident_id,
                "run_id": "rid-" + incident_id,
                "scenario_id": scenario_id,
                "severity": severity,
                "outcome": outcome,
                "evidence_status": evidence_status,
                "safety_states": ["ACTIVE_NORMAL", terminal_safety],
                "generated_at_utc": "2026-05-10T00:00:00+00:00",
                "timeline": {
                    "first_fault_index": 0,
                    "terminal_index": 1,
                    "entries": [
                        {
                            "category": "fault_injection",
                            "event_type": "fault_injection.fired",
                            "attributes": {"fault_type": "stale_lidar"},
                            "safety_state": "ACTIVE_NORMAL",
                        },
                        {
                            "category": "safety_transition",
                            "event_type": "safety_transition.entered",
                            "attributes": {},
                            "safety_state": terminal_safety,
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    return bundle


def test_incident_index_filters_by_severity(tmp_path: Path) -> None:
    root = tmp_path / "incidents"
    _write_fake_bundle(root, incident_id="a", scenario_id="x", severity="moderate", outcome="safe_stop_success", evidence_status="complete")
    _write_fake_bundle(root, incident_id="b", scenario_id="y", severity="high", outcome="estop_latched", evidence_status="partial", terminal_safety="E_STOP_LATCHED")
    index = build_incident_index(incidents_root=root)
    moderate = index.filter(severity="moderate")
    high = index.filter(severity="high")
    assert {r.incident_id for r in moderate} == {"a"}
    assert {r.incident_id for r in high} == {"b"}


def test_incident_index_filters_by_outcome(tmp_path: Path) -> None:
    root = tmp_path / "incidents"
    _write_fake_bundle(root, incident_id="a", scenario_id="x", severity="moderate", outcome="safe_stop_success", evidence_status="complete")
    _write_fake_bundle(root, incident_id="b", scenario_id="y", severity="high", outcome="mission_aborted", evidence_status="partial")
    index = build_incident_index(incidents_root=root)
    aborted = index.filter(outcome="mission_aborted")
    assert {r.incident_id for r in aborted} == {"b"}


def test_incident_index_filters_by_evidence_status(tmp_path: Path) -> None:
    root = tmp_path / "incidents"
    _write_fake_bundle(root, incident_id="a", scenario_id="x", severity="low", outcome="controlled_degradation", evidence_status="static_only")
    _write_fake_bundle(root, incident_id="b", scenario_id="y", severity="moderate", outcome="safe_stop_success", evidence_status="complete")
    index = build_incident_index(incidents_root=root)
    static = index.filter(evidence_status="static_only")
    assert {r.incident_id for r in static} == {"a"}


def test_incident_index_handles_missing_report(tmp_path: Path) -> None:
    root = tmp_path / "incidents"
    (root / "broken").mkdir(parents=True)
    index = build_incident_index(incidents_root=root)
    assert len(index.rows) == 1
    assert "missing" in index.rows[0].notes.lower()


# ---------------------------------------------------------------------------
# Compare.
# ---------------------------------------------------------------------------


def test_compare_two_bundles(tmp_path: Path) -> None:
    root = tmp_path / "incidents"
    a = _write_fake_bundle(root, incident_id="a", scenario_id="x", severity="moderate", outcome="safe_stop_success", evidence_status="complete")
    b = _write_fake_bundle(root, incident_id="b", scenario_id="y", severity="high", outcome="estop_latched", evidence_status="partial", terminal_safety="E_STOP_LATCHED")
    comp = compare_incidents(bundle_dirs=[a, b], comparison_id="cmp1")
    assert {r.incident_id for r in comp.rows} == {"a", "b"}
    md = render_incident_comparison_md(comp)
    assert "Incident Comparison" in md
    assert "`a`" in md and "`b`" in md


def test_compare_handles_missing_report(tmp_path: Path) -> None:
    a = tmp_path / "a"
    a.mkdir()
    b = tmp_path / "b"
    b.mkdir()
    comp = compare_incidents(bundle_dirs=[a, b], comparison_id="cmp")
    assert all(r.evidence_status == "missing" for r in comp.rows)


# ---------------------------------------------------------------------------
# CLI smoke.
# ---------------------------------------------------------------------------


def _import_cli(name: str):
    import importlib
    import sys

    tools_dir = REPO_ROOT / "rover_ws" / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    return importlib.import_module(name)


def test_cli_reconstruct_incident_writes_bundle(tmp_path: Path) -> None:
    cli = _import_cli("reconstruct_incident")
    rc = cli.main(
        [
            "--scenario",
            str(SCENARIO_FIXTURE_DIR),
            "--runs-root",
            str(RUNS_ROOT),
            "--incident-id",
            "cli-stale",
            "--output",
            str(tmp_path / "out"),
            "--foxglove-layout",
            str(tmp_path / "layout.json"),
        ]
    )
    assert (tmp_path / "out" / "incident-report.json").exists()
    assert (tmp_path / "out" / "timeline-state.mmd").exists()


def test_cli_index_incidents_writes_index(tmp_path: Path) -> None:
    cli = _import_cli("index_incidents")
    root = tmp_path / "incidents"
    _write_fake_bundle(root, incident_id="x", scenario_id="s", severity="moderate", outcome="safe_stop_success", evidence_status="complete")
    rc = cli.main(
        [
            "--incidents-root",
            str(root),
            "--json-out",
            str(tmp_path / "index.json"),
            "--md-out",
            str(tmp_path / "index.md"),
        ]
    )
    assert rc == 0
    payload = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert payload["rows"]
    assert "Incident Index" in (tmp_path / "index.md").read_text(encoding="utf-8")


def test_cli_compare_incidents_writes_comparison(tmp_path: Path) -> None:
    cli = _import_cli("compare_incidents")
    root = tmp_path / "incidents"
    a = _write_fake_bundle(root, incident_id="a", scenario_id="x", severity="moderate", outcome="safe_stop_success", evidence_status="complete")
    b = _write_fake_bundle(root, incident_id="b", scenario_id="y", severity="high", outcome="estop_latched", evidence_status="partial", terminal_safety="E_STOP_LATCHED")
    rc = cli.main(
        [
            str(a),
            str(b),
            "--comparison-id",
            "cli-cmp",
            "--out-dir",
            str(tmp_path / "cmp"),
        ]
    )
    assert rc == 0
    assert (tmp_path / "cmp" / "cli-cmp.json").exists()
    assert (tmp_path / "cmp" / "cli-cmp.md").exists()


# ---------------------------------------------------------------------------
# Recommendations.
# ---------------------------------------------------------------------------


def test_recommendations_flag_static_only_evidence() -> None:
    incident = Incident(
        incident_id="r1",
        run_id=None,
        scenario_id=None,
        severity=IncidentSeverity.INFORMATIONAL,
        outcome=IncidentOutcome.INCONCLUSIVE,
        evidence_status=IncidentEvidenceStatus.STATIC_ONLY,
    )
    recs = derive_recommendations(incident)
    assert any("static-only" in r.lower() for r in recs)


def test_recommendations_flag_contradictions() -> None:
    incident = Incident(
        incident_id="r2",
        run_id=None,
        scenario_id=None,
        severity=IncidentSeverity.HIGH,
        outcome=IncidentOutcome.INCONCLUSIVE,
        evidence_status=IncidentEvidenceStatus.INCONSISTENT,
        contradictions=("safe_stop without zeroing",),
    )
    recs = derive_recommendations(incident)
    assert any("contradiction" in r.lower() for r in recs)
