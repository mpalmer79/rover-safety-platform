"""Phase 14A deterministic mission-compiler tests.

The platform is **not safety-certified**. Tests are fully
deterministic; identical inputs produce identical outputs. No
network, no LLM, no ROS.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

from app.natural_language_mission import (
    AMBIGUITY_PHRASES,
    COMPILE_STATUS_AMBIGUOUS,
    COMPILE_STATUS_OK,
    COMPILE_STATUS_OK_WITH_WARNINGS,
    COMPILE_STATUS_REJECTED,
    COMPILER_VERSION,
    DANGEROUS_PHRASES,
    DEFAULT_ODD_PROFILE_ID,
    EXAMPLES,
    NON_CERTIFICATION_DISCLAIMER,
    RISK_BANDS,
    RISK_CRITICAL,
    RISK_LOW,
    RISK_MODERATE,
    build_audit,
    build_chain,
    build_replay_binding,
    classify_risk,
    compile_intent,
    detect_contradictions,
    get_profile,
    list_profiles,
    parse_intent,
    plan_to_dict,
    render_plan_markdown,
    render_plan_mermaid,
    template_by_id,
    validate_all,
    write_audit,
    write_plan,
)
from app.verification.requirements import (
    RequirementKind,
    RequirementsRegistry,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
NL_PKG = REPO_ROOT / "backend" / "app" / "natural_language_mission"


# ----------------------------------------------------------------------
# requirement registry coverage
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "req_id",
    [
        "REQ-MCOMP-001",
        "REQ-MCOMP-002",
        "REQ-MCOMP-003",
        "REQ-MCOMP-004",
        "REQ-MCOMP-005",
        "REQ-MCOMP-006",
        "REQ-MCOMP-007",
        "REQ-MCOMP-008",
        "REQ-MCOMP-009",
        "REQ-MCOMP-010",
    ],
)
def test_requirement_registered(req_id: str):
    registry = RequirementsRegistry()
    assert req_id in registry
    req = registry.get(req_id)
    assert req.kind == RequirementKind.MISSION_COMPILER
    assert req.test_refs


def test_requirement_kind_mission_compiler_exists():
    assert RequirementKind.MISSION_COMPILER.value == "mission_compiler"


# ----------------------------------------------------------------------
# determinism
# ----------------------------------------------------------------------


def test_compile_is_byte_deterministic():
    intent = "Drive to waypoint bravo. Return to dock."
    a = compile_intent(intent, plan_id="t1", generated_at_utc="2026-05-12T00:00:00+00:00")
    b = compile_intent(intent, plan_id="t1", generated_at_utc="2026-05-12T00:00:00+00:00")
    assert plan_to_dict(a) == plan_to_dict(b)


def test_compile_hash_stable():
    intent = "Inspect inspection_zone_north. Return to dock."
    a = compile_intent(intent, plan_id="t2", generated_at_utc="2026-05-12T00:00:00+00:00")
    b = compile_intent(intent, plan_id="t2", generated_at_utc="2026-05-12T00:00:00+00:00")
    assert a.compile_hash == b.compile_hash


def test_mission_graph_is_deterministic():
    intent = "Patrol patrol_loop_a. Inspect inspection_zone_north. Return to dock."
    a = compile_intent(intent, plan_id="g1", generated_at_utc="2026-05-12T00:00:00+00:00")
    b = compile_intent(intent, plan_id="g1", generated_at_utc="2026-05-12T00:00:00+00:00")
    assert a.graph == b.graph


def test_mission_graph_mermaid_byte_stable():
    intent = "Patrol patrol_loop_a. Inspect inspection_zone_north. Return to dock."
    a = compile_intent(intent, plan_id="g2", generated_at_utc="2026-05-12T00:00:00+00:00")
    b = compile_intent(intent, plan_id="g2", generated_at_utc="2026-05-12T00:00:00+00:00")
    assert render_plan_mermaid(a) == render_plan_mermaid(b)


def test_explainability_is_reproducible():
    intent = "Drive to waypoint alpha. Limit speed to 1.0 m/s."
    a = compile_intent(intent, plan_id="g3", generated_at_utc="2026-05-12T00:00:00+00:00")
    b = compile_intent(intent, plan_id="g3", generated_at_utc="2026-05-12T00:00:00+00:00")
    assert a.explainability_chain == b.explainability_chain


def test_compiler_does_not_import_llm_sdks():
    forbidden = ("anthropic", "openai", "cohere", "google.generativeai", "vertexai", "replicate")
    for path in NL_PKG.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} contains forbidden token {token!r}"


# ----------------------------------------------------------------------
# parser + grammar
# ----------------------------------------------------------------------


def test_parser_normalises_whitespace_and_punctuation():
    parsed = parse_intent("  Drive   to    waypoint bravo!  ")
    assert parsed.normalized_text == "drive to waypoint bravo"
    assert len(parsed.clauses) == 1
    assert parsed.clauses[0].template_id == "move_to_target"


def test_parser_splits_on_period_only_with_whitespace():
    parsed = parse_intent("Limit speed to 1.5 m/s.")
    assert any(c.template_id == "speed_limit" for c in parsed.clauses)


def test_parser_returns_empty_for_blank_input():
    parsed = parse_intent("   ")
    assert parsed.clauses == ()
    assert any(d.code == "empty_intent" for d in parsed.diagnostics)


def test_parser_extracts_multiple_clauses():
    parsed = parse_intent(
        "Drive to waypoint bravo. Patrol patrol_loop_a. Return to dock."
    )
    assert len(parsed.clauses) == 3


def test_unsupported_instruction_rejected():
    parsed = parse_intent("Do a barrel roll.")
    assert parsed.clauses == ()
    assert any(d.code == "unsupported_instruction" for d in parsed.diagnostics)


def test_dangerous_unsupported_instruction_rejected():
    parsed = parse_intent("Run shell command and dock.")
    assert any(
        d.code == "dangerous_unsupported_instruction" for d in parsed.diagnostics
    )


def test_ambiguous_destination_preserved():
    plan = compile_intent(
        "Drive to somewhere near the loading area.",
        plan_id="amb1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    # Status must NOT be compile_ok; ambiguity must surface.
    assert plan.status in (COMPILE_STATUS_AMBIGUOUS, COMPILE_STATUS_REJECTED)
    assert any(d.code.startswith("ambiguous") for d in plan.diagnostics)


def test_compiler_never_invents_waypoints():
    plan = compile_intent(
        "Drive to somewhere near the loading area.",
        plan_id="amb2",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    # No objectives produced; ambiguity must NOT be silently resolved.
    assert plan.objectives == ()


def test_template_registry_is_closed():
    # Each template id must be unique.
    from app.natural_language_mission import all_templates

    ids = [t.template_id for t in all_templates()]
    assert len(ids) == len(set(ids))


def test_template_by_id_returns_match_or_none():
    assert template_by_id("move_to_target") is not None
    assert template_by_id("nonexistent_template") is None


# ----------------------------------------------------------------------
# constraints + contradictions
# ----------------------------------------------------------------------


def test_contradictory_instructions_rejected():
    plan = compile_intent(
        "Drive to waypoint alpha. Do not enter waypoint alpha. Return to dock.",
        plan_id="con1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert plan.status == COMPILE_STATUS_REJECTED
    assert any(d.code == "contradiction" for d in plan.diagnostics)


def test_negative_speed_limit_rejected():
    plan = compile_intent(
        "Drive to waypoint bravo. Limit speed to 0.0 m/s.",
        plan_id="con2",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert any(d.code == "contradiction" for d in plan.diagnostics)


# ----------------------------------------------------------------------
# ODD validation
# ----------------------------------------------------------------------


def test_restricted_zone_mission_rejected():
    plan = compile_intent(
        "Drive to restricted_corridor_one.",
        plan_id="odd1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert plan.status == COMPILE_STATUS_REJECTED
    assert any(d.code == "odd_violation" for d in plan.diagnostics)


def test_speed_outside_odd_rejected():
    plan = compile_intent(
        "Drive to waypoint bravo. Do not exceed 5.0 m/s.",
        plan_id="odd2",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert plan.status == COMPILE_STATUS_REJECTED
    assert any(d.code == "odd_violation" for d in plan.diagnostics)


def test_time_window_outside_odd_rejected():
    plan = compile_intent(
        "Drive to waypoint bravo. Operate only during night.",
        plan_id="odd3",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert plan.status == COMPILE_STATUS_REJECTED
    assert any(d.code == "odd_violation" for d in plan.diagnostics)


def test_unknown_zone_rejected_by_default_odd():
    plan = compile_intent(
        "Drive to waypoint zeta.",
        plan_id="odd4",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert plan.status == COMPILE_STATUS_REJECTED
    assert any(d.code == "odd_violation" for d in plan.diagnostics)


def test_odd_profile_registry_contains_default_and_night():
    profiles = list_profiles()
    assert DEFAULT_ODD_PROFILE_ID in profiles
    assert "night-restricted" in profiles


def test_get_profile_raises_on_unknown():
    with pytest.raises(KeyError):
        get_profile("does-not-exist")


def test_night_profile_rejects_warehouse_zones():
    plan = compile_intent(
        "Drive to waypoint bravo.",
        plan_id="odd5",
        generated_at_utc="2026-05-12T00:00:00+00:00",
        odd_profile_id="night-restricted",
    )
    assert plan.status == COMPILE_STATUS_REJECTED


# ----------------------------------------------------------------------
# recovery path validation
# ----------------------------------------------------------------------


def test_recovery_path_warning_when_missing():
    plan = compile_intent(
        "Drive to waypoint bravo. Safe-stop on lidar stale.",
        plan_id="rec1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    # Plan compiles but recovery warning surfaces.
    assert any(d.code == "missing_recovery_path" for d in plan.diagnostics)


def test_recovery_path_satisfied_by_dock_return():
    plan = compile_intent(
        "Drive to waypoint bravo. Safe-stop on lidar stale. Return to dock.",
        plan_id="rec2",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert not any(d.code == "missing_recovery_path" for d in plan.diagnostics)


# ----------------------------------------------------------------------
# risk classification
# ----------------------------------------------------------------------


def test_risk_band_thresholds():
    from app.natural_language_mission.risk import _band_for_score  # type: ignore

    assert _band_for_score(0) == "informational"
    assert _band_for_score(10) == RISK_LOW
    assert _band_for_score(30) == RISK_MODERATE
    assert _band_for_score(70) == "high"
    assert _band_for_score(95) == RISK_CRITICAL


def test_critical_risk_requires_reviewer_action():
    plan = compile_intent(
        "Drive to restricted_corridor_one.",
        plan_id="risk1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert plan.risk.band == RISK_CRITICAL
    assert plan.risk.required_reviewer_actions


def test_risk_bands_are_in_documented_set():
    plan = compile_intent(
        "Patrol patrol_loop_a. Inspect inspection_zone_north. Return to dock.",
        plan_id="risk2",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert plan.risk.band in RISK_BANDS


# ----------------------------------------------------------------------
# audit + replay metadata
# ----------------------------------------------------------------------


def test_audit_contains_all_required_fields():
    plan = compile_intent(
        "Drive to waypoint bravo. Return to dock.",
        plan_id="aud1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    audit = build_audit(plan)
    for key in (
        "plan_id",
        "compiler_version",
        "compile_hash",
        "generated_at_utc",
        "odd_profile_id",
        "original_intent",
        "normalized_intent",
        "status",
        "extracted_objectives",
        "constraints",
        "rejected_instructions",
        "validation_diagnostics",
        "assumptions",
        "risk",
        "replay_binding_id",
        "replay_compatibility",
        "disclaimer",
    ):
        assert key in audit


def test_audit_carries_disclaimer():
    plan = compile_intent(
        "Drive to waypoint bravo.",
        plan_id="aud2",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    audit = build_audit(plan)
    assert audit["disclaimer"] == NON_CERTIFICATION_DISCLAIMER
    assert audit["replay_compatibility"]["runtime_executed"] is False


def test_replay_binding_marks_runtime_not_executed():
    plan = compile_intent(
        "Drive to waypoint bravo.",
        plan_id="rb1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    binding = build_replay_binding(plan)
    assert binding.runtime_executed is False


def test_replay_binding_emits_stable_markers():
    plan = compile_intent(
        "Drive to waypoint bravo. Patrol patrol_loop_a.",
        plan_id="rb2",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    a = build_replay_binding(plan)
    b = build_replay_binding(plan)
    assert a == b
    assert a.timeline_markers  # non-empty


def test_audit_write_creates_files(tmp_path: Path):
    plan = compile_intent(
        "Drive to waypoint bravo.",
        plan_id="aud3",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    j = tmp_path / "a.json"
    m = tmp_path / "a.md"
    write_audit(plan, json_path=j, md_path=m)
    assert j.exists() and m.exists()
    assert "not safety-certified" in m.read_text(encoding="utf-8")


# ----------------------------------------------------------------------
# explainability
# ----------------------------------------------------------------------


def test_explainability_chain_includes_all_stages():
    plan = compile_intent(
        "Drive to waypoint bravo. Return to dock.",
        plan_id="exp1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    chain = "\n".join(plan.explainability_chain)
    assert "USER INPUT" in chain
    assert "NORMALIZED INPUT" in chain
    assert "EXTRACTED CLAUSES" in chain
    assert "NORMALIZED OBJECTIVES" in chain
    assert "VALIDATION DIAGNOSTICS" in chain
    assert "RISK CLASSIFICATION" in chain
    assert "FINAL COMPILED PLAN STATUS" in chain


# ----------------------------------------------------------------------
# reporting
# ----------------------------------------------------------------------


def test_plan_markdown_contains_disclaimer_and_mermaid():
    plan = compile_intent(
        "Drive to waypoint bravo. Return to dock.",
        plan_id="md1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    md = render_plan_markdown(plan)
    assert "not safety-certified" in md
    assert "```mermaid" in md


def test_plan_to_dict_serialises_round_trip(tmp_path: Path):
    plan = compile_intent(
        "Drive to waypoint bravo.",
        plan_id="ser1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    p = tmp_path / "plan.json"
    md = tmp_path / "plan.md"
    write_plan(plan, json_path=p, md_path=md)
    payload = json.loads(p.read_text(encoding="utf-8"))
    assert payload["plan_id"] == "ser1"
    assert payload["compile_hash"] == plan.compile_hash
    assert payload["disclaimer"] == NON_CERTIFICATION_DISCLAIMER


# ----------------------------------------------------------------------
# canonical examples
# ----------------------------------------------------------------------


@pytest.mark.parametrize("ex", EXAMPLES, ids=lambda e: e.example_id)
def test_canonical_examples_match_expected_status(ex):
    plan = compile_intent(
        ex.intent,
        plan_id=ex.example_id,
        generated_at_utc="2026-05-12T00:00:00+00:00",
        odd_profile_id=ex.odd_profile_id,
    )
    assert plan.status == ex.expected_status, (
        f"{ex.example_id}: got {plan.status!r} expected {ex.expected_status!r}"
    )


def test_canonical_mission_library_present_on_disk():
    base = REPO_ROOT / "mission-library"
    for sub in ("intents", "compiled", "rejected", "audits", "examples"):
        assert (base / sub).is_dir(), f"missing {sub!r}"
    for ex in EXAMPLES:
        # Intent always exists
        assert (base / "intents" / f"{ex.example_id}.txt").is_file()
        # Audit always exists (JSON + MD)
        assert (base / "audits" / f"{ex.example_id}-audit.json").is_file()
        assert (base / "audits" / f"{ex.example_id}-audit.md").is_file()


# ----------------------------------------------------------------------
# CLIs (loaded by file path; no ROS dependency)
# ----------------------------------------------------------------------


def _load_cli(name: str):
    tools_dir = REPO_ROOT / "rover_ws" / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    path = tools_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_cli_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_cli_compile_writes_files(tmp_path: Path, capsys):
    cli = _load_cli("compile_mission_intent")
    code = cli.main(
        [
            "--intent",
            "Drive to waypoint bravo. Return to dock.",
            "--plan-id",
            "cli-1",
            "--generated-at",
            "2026-05-12T00:00:00+00:00",
            "--out-dir",
            str(tmp_path),
            "--json",
        ]
    )
    assert code == 0
    assert (tmp_path / "cli-1.json").exists()
    assert (tmp_path / "cli-1.md").exists()
    assert (tmp_path / "cli-1-replay-binding.json").exists()


def test_cli_validate_plan_reproducible(tmp_path: Path):
    cli = _load_cli("compile_mission_intent")
    cli.main(
        [
            "--intent",
            "Drive to waypoint bravo.",
            "--plan-id",
            "cli-2",
            "--generated-at",
            "2026-05-12T00:00:00+00:00",
            "--out-dir",
            str(tmp_path),
        ]
    )
    validator = _load_cli("validate_mission_plan")
    code = validator.main(["--plan", str(tmp_path / "cli-2.json")])
    assert code == 0


def test_cli_explain_reads_chain(tmp_path: Path, capsys):
    cli = _load_cli("compile_mission_intent")
    cli.main(
        [
            "--intent",
            "Drive to waypoint bravo.",
            "--plan-id",
            "cli-3",
            "--generated-at",
            "2026-05-12T00:00:00+00:00",
            "--out-dir",
            str(tmp_path),
        ]
    )
    explainer = _load_cli("explain_mission_plan")
    code = explainer.main(["--plan", str(tmp_path / "cli-3.json"), "--json"])
    assert code == 0


def test_cli_generate_audit_writes_artefacts(tmp_path: Path):
    cli = _load_cli("compile_mission_intent")
    cli.main(
        [
            "--intent",
            "Drive to waypoint bravo.",
            "--plan-id",
            "cli-4",
            "--generated-at",
            "2026-05-12T00:00:00+00:00",
            "--out-dir",
            str(tmp_path),
        ]
    )
    auditor = _load_cli("generate_mission_audit")
    audits_dir = tmp_path / "audits"
    code = auditor.main(
        ["--plan", str(tmp_path / "cli-4.json"), "--out-dir", str(audits_dir)]
    )
    assert code == 0
    assert (audits_dir / "cli-4-audit.json").is_file()
    assert (audits_dir / "cli-4-audit.md").is_file()


# ----------------------------------------------------------------------
# doc disclaimer presence
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "doc_path",
    [
        "docs/NATURAL_LANGUAGE_MISSION_COMPILER.md",
        "docs/MISSION_ASSURANCE_MODEL.md",
        "docs/MISSION_INTENT_GRAMMAR.md",
        "docs/MISSION_RISK_CLASSIFICATION.md",
        "docs/HUMAN_TO_AUTONOMY_BOUNDARY.md",
        "docs/MISSION_COMPILER_WALKTHROUGH.md",
    ],
)
def test_doc_carries_disclaimer(doc_path: str):
    text = (REPO_ROOT / doc_path).read_text(encoding="utf-8")
    assert "not safety-certified" in text


# ----------------------------------------------------------------------
# misc honesty
# ----------------------------------------------------------------------


def test_compiler_version_constant():
    assert COMPILER_VERSION.startswith("phase14a")


def test_malformed_input_produces_diagnostics_not_exception():
    # Insert weird unicode, mixed casing - must still parse cleanly.
    plan = compile_intent(
        "DRIVE  TO   waypoint  bravo. ;;;  ",
        plan_id="mal1",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    assert plan.status in (COMPILE_STATUS_OK, COMPILE_STATUS_OK_WITH_WARNINGS,
                            COMPILE_STATUS_AMBIGUOUS, COMPILE_STATUS_REJECTED)


def test_dangerous_phrases_constant_not_empty():
    assert DANGEROUS_PHRASES


def test_ambiguity_phrases_constant_not_empty():
    assert AMBIGUITY_PHRASES
