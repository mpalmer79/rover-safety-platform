"""Bounded grammar templates for the mission compiler.

The platform is **not safety-certified**. The template registry is
the *closed* set of constructs the compiler accepts. Anything that
fails to match a template is recorded as
``unsupported_instruction`` and never translated into a mission
objective or constraint.

Each template is a deterministic pattern with:

* a stable ``template_id``,
* a list of pre-compiled regex patterns,
* a slot extractor that produces a normalised payload,
* a category (``objective`` / ``constraint`` / ``stop_directive``).

Templates are intentionally narrow. Adding a template is a
deliberate, reviewable change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Mapping


@dataclass(frozen=True)
class Template:
    template_id: str
    category: str
    patterns: tuple[re.Pattern[str], ...]
    extractor: Callable[[re.Match[str]], Mapping[str, str]]
    description: str


_LOCATOR_PREFIXES = ("waypoint ", "zone ", "area ", "region ", "checkpoint ")


def _strip_locator(value: str) -> str:
    v = value.strip()
    for pfx in _LOCATOR_PREFIXES:
        if v.startswith(pfx):
            v = v[len(pfx):]
    return v


def _slot_target(m: re.Match[str]) -> Mapping[str, str]:
    return {"target": _strip_locator(m.group("target"))}


def _slot_zone(m: re.Match[str]) -> Mapping[str, str]:
    return {"zone": _strip_locator(m.group("zone"))}


def _slot_region(m: re.Match[str]) -> Mapping[str, str]:
    return {"region": _strip_locator(m.group("region"))}


def _slot_condition(m: re.Match[str]) -> Mapping[str, str]:
    return {"condition": m.group("condition").strip()}


def _slot_speed_limit(m: re.Match[str]) -> Mapping[str, str]:
    return {"limit_mps": m.group("limit").strip()}


def _slot_time_window(m: re.Match[str]) -> Mapping[str, str]:
    return {"window": m.group("window").strip()}


def _slot_recovery(m: re.Match[str]) -> Mapping[str, str]:
    return {"trigger": m.group("trigger").strip()}


def _slot_empty(m: re.Match[str]) -> Mapping[str, str]:
    return {}


# Stable, narrow regexes. Each pattern is anchored at the start of
# the (lower-cased, stripped) clause so spurious prefixes don't
# match. Whitespace is normalised by the parser before matching.

_TEMPLATES: tuple[Template, ...] = (
    Template(
        template_id="move_to_target",
        category="objective",
        patterns=(
            re.compile(r"^(?:go|drive|move|navigate|proceed) to (?:waypoint |zone )?(?P<target>[a-z0-9 _\-]+?)$"),
            re.compile(r"^head to (?:waypoint |zone )?(?P<target>[a-z0-9 _\-]+?)$"),
        ),
        extractor=_slot_target,
        description="Drive to a named waypoint or zone.",
    ),
    Template(
        template_id="patrol_area",
        category="objective",
        patterns=(
            re.compile(r"^patrol (?:area |zone )?(?P<zone>[a-z0-9 _\-]+?)$"),
            re.compile(r"^patrol the (?P<zone>[a-z0-9 _\-]+?)$"),
        ),
        extractor=_slot_zone,
        description="Patrol a named area.",
    ),
    Template(
        template_id="inspect_zone",
        category="objective",
        patterns=(
            re.compile(r"^inspect (?:zone |area )?(?P<zone>[a-z0-9 _\-]+?)$"),
            re.compile(r"^inspect the (?P<zone>[a-z0-9 _\-]+?)$"),
        ),
        extractor=_slot_zone,
        description="Inspect a named zone.",
    ),
    Template(
        template_id="return_to_dock",
        category="objective",
        patterns=(
            re.compile(r"^return to (?:the )?dock$"),
            re.compile(r"^return home$"),
            re.compile(r"^dock$"),
        ),
        extractor=_slot_empty,
        description="Return to the dock.",
    ),
    Template(
        template_id="wait_for_condition",
        category="objective",
        patterns=(
            re.compile(r"^wait for (?P<condition>[a-z0-9 _\-]+?)$"),
            re.compile(r"^hold until (?P<condition>[a-z0-9 _\-]+?)$"),
        ),
        extractor=_slot_condition,
        description="Wait at the current position for a named condition.",
    ),
    Template(
        template_id="pause_at_checkpoint",
        category="objective",
        patterns=(
            re.compile(r"^pause at (?:checkpoint |waypoint )?(?P<target>[a-z0-9 _\-]+?)$"),
        ),
        extractor=_slot_target,
        description="Pause at a named checkpoint.",
    ),
    Template(
        template_id="terminate_mission",
        category="stop_directive",
        patterns=(
            re.compile(r"^terminate mission$"),
            re.compile(r"^abort mission$"),
            re.compile(r"^stop$"),
        ),
        extractor=_slot_empty,
        description="Terminate the mission cleanly.",
    ),
    Template(
        template_id="avoid_region",
        category="constraint",
        patterns=(
            re.compile(r"^avoid (?:region |area |zone )?(?P<region>[a-z0-9 _\-]+?)$"),
            re.compile(r"^stay out of (?:region |area |zone )?(?P<region>[a-z0-9 _\-]+?)$"),
            re.compile(r"^do not enter (?:region |area |zone )?(?P<region>[a-z0-9 _\-]+?)$"),
        ),
        extractor=_slot_region,
        description="Avoid a named region.",
    ),
    Template(
        template_id="restricted_corridor_avoidance",
        category="constraint",
        patterns=(
            re.compile(r"^avoid restricted corridors?$"),
            re.compile(r"^stay clear of restricted corridors?$"),
        ),
        extractor=_slot_empty,
        description="Avoid restricted corridors.",
    ),
    Template(
        template_id="speed_limit",
        category="constraint",
        patterns=(
            re.compile(r"^limit speed to (?P<limit>\d+(?:\.\d+)?) m/?s?$"),
            re.compile(r"^do not exceed (?P<limit>\d+(?:\.\d+)?) m/?s?$"),
            re.compile(r"^speed limit (?P<limit>\d+(?:\.\d+)?) m/?s?$"),
        ),
        extractor=_slot_speed_limit,
        description="Apply a speed limit in m/s.",
    ),
    Template(
        template_id="time_window",
        category="constraint",
        patterns=(
            re.compile(r"^operate only during (?P<window>[a-z ]+)$"),
            re.compile(r"^operate during (?P<window>[a-z ]+) only$"),
        ),
        extractor=_slot_time_window,
        description="Restrict operation to a named time window.",
    ),
    Template(
        template_id="safe_stop_on_trigger",
        category="constraint",
        patterns=(
            re.compile(r"^safe[- ]stop on (?P<trigger>[a-z0-9 _\-]+?)$"),
            re.compile(r"^safe[- ]stop if (?P<trigger>[a-z0-9 _\-]+?)$"),
        ),
        extractor=_slot_recovery,
        description="Force safe-stop on a named trigger condition.",
    ),
    Template(
        template_id="recovery_directive_return_to_dock",
        category="constraint",
        patterns=(
            re.compile(r"^return to (?:the )?dock if (?P<trigger>[a-z0-9 _\-]+?)$"),
            re.compile(r"^if (?P<trigger>[a-z0-9 _\-]+?) return to (?:the )?dock$"),
        ),
        extractor=_slot_recovery,
        description="Return to dock when a named trigger fires.",
    ),
    Template(
        template_id="continue_under_degraded",
        category="constraint",
        patterns=(
            re.compile(r"^continue under degraded conditions$"),
            re.compile(r"^proceed in degraded mode$"),
        ),
        extractor=_slot_empty,
        description="Allow continuation in degraded mode.",
    ),
)


# ---------------------------------------------------------------------
# DANGEROUS_PHRASES is **signaling and deterrence**, not enforcement.
#
# The actual enforcement is the *whitelist* of mission templates above:
# any clause that does not match a template is routed to ``rejected``
# regardless of whether it contains a "dangerous" phrase. The blocklist
# below earns its keep by producing a clearer reason code
# (``dangerous_unsupported_instruction``) when a clause matches a known
# unsafe shape - useful for operator feedback and for incident triage.
#
# Do NOT expand this blocklist as a primary defence. Adding more
# phrases reinforces the wrong invariant; the right answer when a new
# unsafe instruction shape appears is to leave it un-matched by any
# whitelist template, which is already the reject path.
# ---------------------------------------------------------------------
DANGEROUS_PHRASES: tuple[str, ...] = (
    "run shell",
    "execute python",
    "execute code",
    "rm -rf",
    "shutdown the rover",
    "disable safety",
    "bypass supervisor",
    "override safety",
    "ignore safety",
    "open browser",
    "open ssh",
    "curl ",
    "wget ",
)


# Phrases that almost certainly signal ambiguity (vague locators).
AMBIGUITY_PHRASES: tuple[str, ...] = (
    "somewhere near",
    "around the",
    "near the",
    "approximately near",
    "approximately at",
    "in the general area",
    "wherever",
    "anywhere",
    "kind of near",
    "sort of",
)


def all_templates() -> tuple[Template, ...]:
    return _TEMPLATES


def template_by_id(template_id: str) -> Template | None:
    for t in _TEMPLATES:
        if t.template_id == template_id:
            return t
    return None


def match_clause(clause: str) -> tuple[Template, re.Match[str]] | None:
    """Return the first matching template (and its regex match) or None."""

    norm = clause.strip().lower()
    for template in _TEMPLATES:
        for pat in template.patterns:
            m = pat.match(norm)
            if m:
                return template, m
    return None


__all__ = [
    "Template",
    "all_templates",
    "template_by_id",
    "match_clause",
    "DANGEROUS_PHRASES",
    "AMBIGUITY_PHRASES",
]
