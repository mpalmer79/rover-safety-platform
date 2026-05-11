"""Tests for the requirement registry.

The registry is the seat of traceability discipline: every
requirement must have a stable ID, an architecture reference, and at
least one binding into either tests or scenarios. These tests catch
the most common regressions: duplicate IDs, missing references,
unknown scenario IDs, malformed test paths.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.verification.requirements import (
    REQUIREMENTS,
    Requirement,
    RequirementKind,
    RequirementsRegistry,
    requirement_by_id,
)
from app.verification.scenario_verifier import SCENARIO_EXPECTATIONS


def test_registry_has_at_least_one_requirement_per_kind() -> None:
    registry = RequirementsRegistry(REQUIREMENTS)
    for kind in (
        RequirementKind.SAFETY,
        RequirementKind.FAULT,
        RequirementKind.REPLAY,
        RequirementKind.MISSION,
        RequirementKind.WORLD,
        RequirementKind.DIAGNOSTICS,
        RequirementKind.OPERATOR,
    ):
        assert registry.by_kind(kind), f"no requirements for {kind.value}"


def test_no_duplicate_requirement_ids() -> None:
    ids = [r.req_id for r in REQUIREMENTS]
    assert len(ids) == len(set(ids))


def test_every_requirement_has_an_architecture_ref() -> None:
    for r in REQUIREMENTS:
        assert r.architecture_refs, f"{r.req_id} missing architecture_refs"


def test_every_requirement_has_either_test_or_scenario_coverage() -> None:
    for r in REQUIREMENTS:
        assert r.test_refs or r.scenario_refs, (
            f"{r.req_id} has neither tests nor scenarios"
        )


def test_requirement_scenario_refs_resolve_to_known_scenarios() -> None:
    known = {e.scenario_id for e in SCENARIO_EXPECTATIONS}
    # Some scenario refs may refer to scenarios that exist in the
    # backend/scenarios/ directory but not in the verification
    # expectations. We accept either: scenario file present OR
    # expectation present. Otherwise, fail.
    scenarios_dir = Path(__file__).resolve().parents[1] / "scenarios"
    scenario_files = {p.stem for p in scenarios_dir.glob("*.json")}
    for r in REQUIREMENTS:
        for sid in r.scenario_refs:
            assert sid in known or sid in scenario_files, (
                f"{r.req_id} references unknown scenario_id {sid!r}"
            )


def test_requirement_test_refs_have_expected_format() -> None:
    # Backend / rover_ws tests live in pytest modules (.py). Phase 17A's
    # mission-control UI is verified by vitest (.test.ts / .test.tsx);
    # both module shapes are acceptable as long as the ``::`` separator
    # is present so the reference is unambiguous.
    allowed_suffixes = (".py", ".test.ts", ".test.tsx")
    for r in REQUIREMENTS:
        for ref in r.test_refs:
            assert "::" in ref, f"{r.req_id} test ref {ref!r} missing '::'"
            module_part, _ = ref.split("::", 1)
            assert module_part.endswith(allowed_suffixes), (
                f"{r.req_id} test ref {ref!r} module not in {allowed_suffixes}"
            )


def test_requirement_by_id_lookup() -> None:
    r = requirement_by_id("REQ-SAFE-001")
    assert r.req_id == "REQ-SAFE-001"
    with pytest.raises(KeyError):
        requirement_by_id("REQ-DOES-NOT-EXIST")


def test_registry_to_dict_round_trip() -> None:
    registry = RequirementsRegistry(REQUIREMENTS)
    d = registry.to_dict()
    assert "requirements" in d
    assert len(d["requirements"]) == len(REQUIREMENTS)


def test_registry_rejects_duplicate_ids_when_constructed() -> None:
    a = REQUIREMENTS[0]
    duplicate = Requirement(
        req_id=a.req_id,
        kind=a.kind,
        title="dup",
        description="dup",
        architecture_refs=("ARCHITECTURE.md",),
        test_refs=("backend/tests/test_x.py::test_x",),
    )
    with pytest.raises(ValueError):
        RequirementsRegistry((a, duplicate))
