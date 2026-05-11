"""Normalize raw LLM provider output before validation.

The Phase 15B providers return free-form text; the Phase 19
normalizer strips markdown fences, extracts JSON envelopes from
mixed prose, normalises topic/skill labels, and preserves the raw
payload + any normalization warnings.

The normalizer is **deterministic** and **never** changes the
candidate's semantics — only its shape. If the candidate cannot be
parsed into a recognisable shape the normalizer rejects
deterministically and surfaces the raw payload to the audit.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping


NORMALIZATION_STATUS_ACCEPTED: str = "accepted"
NORMALIZATION_STATUS_REJECTED: str = "rejected"

_FENCE_RE = re.compile(r"^```[a-zA-Z0-9_-]*\n?|\n?```$", re.MULTILINE)
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)

# Topic / skill label aliases. Keys are produced VERBATIM upstream.
_TOPIC_ALIASES: Mapping[str, str] = {
    "cmd_vel": "/cmd_vel",
    "cmd_vel_requested": "/cmd_vel_requested",
    "/cmdvel": "/cmd_vel",
    "/cmdvel_requested": "/cmd_vel_requested",
}

_SKILL_TYPE_ALIASES: Mapping[str, str] = {
    "move forward": "move_forward",
    "move-forward": "move_forward",
    "rotate-in-place": "rotate_in_place",
    "rotate in place": "rotate_in_place",
    "stop-immediately": "stop_immediately",
    "stop immediately": "stop_immediately",
    "stop now": "stop_immediately",
}

_LANGUAGE_ALIASES: Mapping[str, str] = {
    "python": "python_ros2",
    "python3": "python_ros2",
    "python ros2": "python_ros2",
    "ros2-python": "python_ros2",
    "yaml": "yaml_template",
}


@dataclass(frozen=True)
class NormalizationResult:
    """Outcome of a single normalization pass.

    ``status`` is one of ``NORMALIZATION_STATUS_*``. When
    ``accepted`` the ``normalized`` payload is safe to hand to the
    sanitizer + validator; when ``rejected`` ``reason_codes``
    explain why and the raw payload is preserved in
    ``raw_payload``.
    """

    status: str
    accepted: bool
    raw_payload: str
    normalized: Mapping[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()


def _strip_fences(text: str) -> tuple[str, bool]:
    """Remove ```...``` markdown fences if present."""

    if "```" not in text:
        return text, False
    cleaned = _FENCE_RE.sub("", text)
    return cleaned.strip(), True


def _extract_json(text: str) -> tuple[str, bool]:
    """Return the largest JSON-like object substring."""

    candidate = text.strip()
    try:
        json.loads(candidate)
        return candidate, False
    except (json.JSONDecodeError, ValueError):
        pass
    match = _JSON_OBJECT_RE.search(text)
    if match is None:
        return text, False
    return match.group(0), True


def _normalize_value(value: Any, aliases: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        key = value.strip().lower()
        return aliases.get(key, value.strip())
    if isinstance(value, list):
        return [_normalize_value(v, aliases) for v in value]
    return value


def _normalize_payload(payload: Mapping[str, Any]) -> tuple[dict, list[str]]:
    out: dict = dict(payload)
    warnings: list[str] = []

    if "language" in out:
        original = out["language"]
        out["language"] = _normalize_value(original, _LANGUAGE_ALIASES)
        if isinstance(original, str) and out["language"] != original:
            warnings.append(f"language label normalised: {original!r} → {out['language']!r}")

    if "skill_type" in out:
        original = out["skill_type"]
        out["skill_type"] = _normalize_value(original, _SKILL_TYPE_ALIASES)
        if isinstance(original, str) and out["skill_type"] != original:
            warnings.append(
                f"skill_type normalised: {original!r} → {out['skill_type']!r}"
            )

    for key in ("declared_topics", "topics", "requested_topics", "forbidden_topics"):
        if key in out and isinstance(out[key], list):
            normalised = [_normalize_value(v, _TOPIC_ALIASES) for v in out[key]]
            if normalised != out[key]:
                warnings.append(f"topic list normalised in {key!r}")
            out[key] = normalised

    return out, warnings


def normalize_candidate_payload(raw_text: str) -> NormalizationResult:
    """Normalize ``raw_text`` into a structured payload.

    The function never raises; a malformed payload returns a
    ``rejected`` :class:`NormalizationResult` with the raw text
    preserved.
    """

    if not raw_text or not raw_text.strip():
        return NormalizationResult(
            status=NORMALIZATION_STATUS_REJECTED,
            accepted=False,
            raw_payload=raw_text,
            reason_codes=("empty_payload",),
        )

    warnings: list[str] = []
    text, stripped = _strip_fences(raw_text)
    if stripped:
        warnings.append("markdown fences stripped")

    extracted, did_extract = _extract_json(text)
    if did_extract:
        warnings.append("JSON object extracted from mixed prose")

    try:
        parsed = json.loads(extracted)
    except (json.JSONDecodeError, ValueError):
        return NormalizationResult(
            status=NORMALIZATION_STATUS_REJECTED,
            accepted=False,
            raw_payload=raw_text,
            warnings=tuple(warnings),
            reason_codes=("invalid_json",),
        )

    if not isinstance(parsed, dict):
        return NormalizationResult(
            status=NORMALIZATION_STATUS_REJECTED,
            accepted=False,
            raw_payload=raw_text,
            warnings=tuple(warnings),
            reason_codes=("payload_not_object",),
        )

    normalised, more_warnings = _normalize_payload(parsed)
    warnings.extend(more_warnings)

    return NormalizationResult(
        status=NORMALIZATION_STATUS_ACCEPTED,
        accepted=True,
        raw_payload=raw_text,
        normalized=normalised,
        warnings=tuple(warnings),
    )


def normalization_result_to_dict(result: NormalizationResult) -> dict[str, object]:
    return {
        "status": result.status,
        "accepted": result.accepted,
        "raw_payload": result.raw_payload,
        "normalized": dict(result.normalized),
        "warnings": list(result.warnings),
        "reason_codes": list(result.reason_codes),
    }


__all__ = [
    "NORMALIZATION_STATUS_ACCEPTED",
    "NORMALIZATION_STATUS_REJECTED",
    "NormalizationResult",
    "normalization_result_to_dict",
    "normalize_candidate_payload",
]
