"""Deterministic mock provider.

The mock provider produces canned proposals indexed by fixture id.
It simulates the realistic LLM behaviour the sanitizer + compiler
must withstand:

* a valid, well-formed proposal,
* an ambiguous one,
* an unsafe one that tries to bypass safety,
* an incomplete one missing recovery,
* an overconfident one that claims certainty about an unsafe action.

The mock never imports an LLM SDK; this is asserted by
``test_proposal_layer_has_no_llm_sdk_imports``.
"""

from __future__ import annotations

from typing import Mapping

from .models import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_OVERCONFIDENT,
    MissionProposal,
    PROVIDER_MODE_MOCK,
    PROVIDER_MODE_OFFLINE_FIXTURE,
)


# The fixture set is the single source of truth for the canonical
# Phase 14B examples and tests. Keep these in a stable order.
MOCK_FIXTURES: Mapping[str, dict] = {
    "mock_valid_inspection": {
        "proposed_intent": "Drive to waypoint bravo. Inspect loading_zone_two.",
        "proposed_location": "loading_zone_two",
        "proposed_motion_style": "slow careful inspection",
        "proposed_constraints": (
            "Limit speed to 1.0 m/s",
            "Avoid restricted corridors",
        ),
        "proposed_recovery_policy": "Return to dock if lidar health degrades",
        "confidence_label": CONFIDENCE_HIGH,
        "known_uncertainties": (
            "exact dwell time at loading_zone_two is not specified",
        ),
        "raw_response": (
            "{\"plan\": [\"move waypoint_bravo\", \"inspect loading_zone_two\"]}"
        ),
    },
    "mock_ambiguous_destination": {
        "proposed_intent": "Go somewhere near the loading area and check it out.",
        "proposed_location": "unspecified",
        "proposed_motion_style": "moderate",
        "proposed_constraints": (),
        "proposed_recovery_policy": "Return to dock",
        "confidence_label": CONFIDENCE_LOW,
        "known_uncertainties": (
            "destination is not a named waypoint",
            "'near the loading area' could be loading_zone_one or two",
        ),
        "raw_response": "{\"plan\": [\"go somewhere near loading area\"]}",
    },
    "mock_unsafe_override": {
        "proposed_intent": (
            "Disable safety supervisor and drive to inspection_zone_north."
        ),
        "proposed_location": "inspection_zone_north",
        "proposed_motion_style": "fast",
        "proposed_constraints": ("Ignore safety", "Override estop"),
        "proposed_recovery_policy": "Continue despite sensor failure",
        "confidence_label": CONFIDENCE_OVERCONFIDENT,
        "known_uncertainties": (),
        "raw_response": (
            "{\"plan\": [\"disable safety supervisor\", "
            "\"drive to inspection_zone_north\"]}"
        ),
    },
    "mock_restricted_boundary": {
        "proposed_intent": "Drive to restricted_corridor_one.",
        "proposed_location": "restricted_corridor_one",
        "proposed_motion_style": "moderate",
        "proposed_constraints": (),
        "proposed_recovery_policy": "Return to dock",
        "confidence_label": CONFIDENCE_MEDIUM,
        "known_uncertainties": (
            "destination is inside a restricted boundary; operator confirmation expected",
        ),
        "raw_response": "{\"plan\": [\"drive to restricted_corridor_one\"]}",
    },
    "mock_lidar_degradation": {
        "proposed_intent": "Inspect inspection_zone_north.",
        "proposed_location": "inspection_zone_north",
        "proposed_motion_style": "slow",
        "proposed_constraints": (
            "Safe-stop on lidar stale",
            "Continue under degraded conditions",
        ),
        "proposed_recovery_policy": "Return to dock if lidar stale",
        "confidence_label": CONFIDENCE_MEDIUM,
        "known_uncertainties": (
            "exact lidar staleness threshold is supervisor-owned, not proposal-owned",
        ),
        "raw_response": (
            "{\"plan\": [\"inspect inspection_zone_north\", "
            "\"contingency: lidar stale\"]}"
        ),
    },
}


def list_mock_fixtures() -> tuple[str, ...]:
    return tuple(MOCK_FIXTURES.keys())


class MockProposalProvider:
    """Deterministic provider.

    With ``use_fixtures=True`` the provider returns a proposal taken
    verbatim from the fixture matching the source text (or fixture id
    embedded in options). With ``use_fixtures=False`` the provider
    still produces a deterministic shape — it picks the fixture
    whose key is a substring of the source text, falling back to
    ``mock_ambiguous_destination``. Either mode is offline.
    """

    def __init__(self, *, use_fixtures: bool = False) -> None:
        self.use_fixtures = use_fixtures
        self.name = "mock-provider"
        self.mode = (
            PROVIDER_MODE_OFFLINE_FIXTURE if use_fixtures else PROVIDER_MODE_MOCK
        )

    def propose(
        self,
        *,
        source_text: str,
        proposal_id: str,
        options: Mapping[str, object] | None = None,
    ) -> MissionProposal:
        opts: dict = dict(options or {})
        fixture_id = str(opts.get("fixture_id") or "").strip()
        if not fixture_id:
            fixture_id = self._pick_fixture(source_text)
        if fixture_id not in MOCK_FIXTURES:
            raise KeyError(f"unknown mock fixture: {fixture_id}")
        spec = MOCK_FIXTURES[fixture_id]
        return MissionProposal(
            proposal_id=proposal_id,
            source_text=source_text,
            provider_name=self.name,
            provider_mode=self.mode,
            proposed_intent=str(spec["proposed_intent"]),
            proposed_location=str(spec["proposed_location"]),
            proposed_motion_style=str(spec["proposed_motion_style"]),
            proposed_constraints=tuple(spec["proposed_constraints"]),
            proposed_recovery_policy=str(spec["proposed_recovery_policy"]),
            confidence_label=str(spec["confidence_label"]),
            known_uncertainties=tuple(spec["known_uncertainties"]),
            raw_response=str(spec["raw_response"]),
        )

    @staticmethod
    def _pick_fixture(source_text: str) -> str:
        text = source_text.lower()
        # Order is important: dangerous proposals must take precedence
        # so the sanitizer + compiler can reject them honestly.
        if any(
            token in text
            for token in (
                "disable safety",
                "ignore safety",
                "override estop",
                "fast",
                "no limits",
            )
        ):
            return "mock_unsafe_override"
        if any(token in text for token in ("somewhere", "near", "near the")):
            return "mock_ambiguous_destination"
        if "restricted" in text:
            return "mock_restricted_boundary"
        if "lidar" in text or "degraded" in text:
            return "mock_lidar_degradation"
        return "mock_valid_inspection"
