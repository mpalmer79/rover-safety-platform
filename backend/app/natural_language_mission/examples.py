"""Canonical example mission intents.

The platform is **not safety-certified**. These examples are
read-only seeds for the canonical compiled-mission bundle and the
test suite.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntentExample:
    example_id: str
    intent: str
    expected_status: str
    notes: str
    odd_profile_id: str = "default-warehouse"


# Each example is a deliberate fixture; adding one is a deliberate,
# reviewable change.
EXAMPLES: tuple[IntentExample, ...] = (
    IntentExample(
        example_id="warehouse_inspection",
        intent=(
            "Drive to waypoint bravo. Inspect loading_zone_two. "
            "Avoid restricted corridors. Return to dock if lidar "
            "health degrades. Limit speed to 1.0 m/s."
        ),
        expected_status="compile_ok",
        notes="Successful warehouse inspection mission with recovery directive.",
    ),
    IntentExample(
        example_id="patrol_loop",
        intent=(
            "Patrol patrol_loop_a. Pause at checkpoint bravo. "
            "Return to dock."
        ),
        expected_status="compile_ok",
        notes="Successful patrol mission with checkpoint pause.",
    ),
    IntentExample(
        example_id="degraded_lidar_contingency",
        intent=(
            "Inspect inspection_zone_north. Safe-stop on lidar stale. "
            "Continue under degraded conditions. Return to dock if lidar stale."
        ),
        expected_status="compile_ok",
        notes="Mission with degraded-mode contingency + recovery directive.",
    ),
    IntentExample(
        example_id="restricted_zone_rejected",
        intent="Drive to restricted_corridor_one.",
        expected_status="compile_rejected",
        notes="Mission targets a prohibited region; ODD validator rejects.",
    ),
    IntentExample(
        example_id="ambiguous_request",
        intent="Go somewhere near the loading area and check it out.",
        expected_status="compile_rejected",
        notes="Ambiguous destination; the compiler must not invent coordinates.",
    ),
    IntentExample(
        example_id="contradictory_request",
        intent=(
            "Drive to waypoint alpha. Do not enter waypoint alpha. "
            "Return to dock."
        ),
        expected_status="compile_rejected",
        notes="Two clauses disagree about waypoint alpha; compiler rejects.",
    ),
    IntentExample(
        example_id="unsupported_instruction",
        intent="Run shell command rm -rf / and then return to dock.",
        expected_status="compile_rejected",
        notes="Forbidden construct; the compiler rejects it as dangerous.",
    ),
)


def example_by_id(example_id: str) -> IntentExample:
    for ex in EXAMPLES:
        if ex.example_id == example_id:
            return ex
    raise KeyError(example_id)


__all__ = [
    "IntentExample",
    "EXAMPLES",
    "example_by_id",
]
