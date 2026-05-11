"""Deterministic developer-request parser.

The parser classifies a free-text request into one of the supported
``SkillType``s, extracts parameters, or rejects the request. It is
deterministic: identical input yields byte-identical output. It does
not call out to anything, does not import an LLM SDK, and never
fabricates parameter values.

Recognised intents:

* "move forward N feet|metres|meters" -> MOVE_FORWARD_DISTANCE
* "drive/go forward N feet|m" -> MOVE_FORWARD_DISTANCE
* "rotate|turn (left|right) N degrees|deg" -> ROTATE_DEGREES
* "stop immediately|now" -> STOP_IMMEDIATELY
* "keyboard key ... to move/forward" -> KEYBOARD_FORWARD_BINDING
* "controller button ... to stop|move" -> CONTROLLER_BUTTON_BINDING
* "publish requested motion ..." -> PUBLISH_REQUESTED_MOTION
* "go to waypoint <name>" -> WAYPOINT_REQUEST
* "patrol <a> <b> [<c> ...]" -> PATROL_ROUTE_TEMPLATE
* "wrap ... in safe stop" -> SAFE_STOP_WRAPPER

Rejection vocabulary (returns SkillRejectionReason):

* "publish ... cmd_vel" / "cmd_vel directly" -> DIRECT_ACTUATOR_COMMAND
* "disable safety" / "ignore safety" -> SAFETY_OVERRIDE
* "ignore estop" / "override estop" -> ESTOP_OVERRIDE
* "forever" / "infinitely" / "unbounded" -> UNBOUNDED_MOTION
* "as fast as possible" / "max speed" -> UNBOUNDED_SPEED
* "spin motors" / "motor controller" -> DIRECT_MOTOR_CONTROL
* "disable lidar" / "turn off lidar" -> SENSOR_DISABLE
* "shell command" / "run sh" / "execute python|code" -> SHELL_OR_CODE_EXECUTION
* "curl http" / "open socket" -> NETWORK_ACCESS
"""

from __future__ import annotations

import re
from typing import Optional

from .diagnostics import info, rejection, warning
from .models import (
    SkillCandidate,
    SkillDiagnostic,
    SkillGenerationStatus,
    SkillParameter,
    SkillRejectionReason,
    SkillType,
)


# ---------------------------------------------------------------------
# Bounds. These match the catalog's safety_constraints so a parsed
# parameter that is in-range never produces an out-of-range rejection
# downstream.
# ---------------------------------------------------------------------

_MAX_DISTANCE_M: float = 25.0
_MAX_ANGLE_DEG: float = 720.0
_FEET_TO_METERS: float = 0.3048


# ---------------------------------------------------------------------
# Normalisation.
# ---------------------------------------------------------------------

_WHITESPACE_RE = re.compile(r"\s+")
_TRAILING_PUNCT_RE = re.compile(r"[!?.,;:]+$")


def _normalise(text: str) -> str:
    cleaned = text.strip().lower()
    cleaned = _TRAILING_PUNCT_RE.sub("", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    return cleaned


# ---------------------------------------------------------------------
# Rejection rules (run first; rejection always dominates).
# ---------------------------------------------------------------------

_REJECTION_RULES: tuple[tuple[str, str, str], ...] = (
    (
        r"\bpublish\s+(?:directly\s+)?to\s+/?cmd_vel\b",
        SkillRejectionReason.DIRECT_ACTUATOR_COMMAND.value,
        "Direct actuator publication is forbidden; use /cmd_vel_requested.",
    ),
    (
        r"\bcmd_vel\s+directly\b",
        SkillRejectionReason.DIRECT_ACTUATOR_COMMAND.value,
        "Direct actuator publication is forbidden; use /cmd_vel_requested.",
    ),
    (
        r"\b/cmd_vel(?!_requested)\b",
        SkillRejectionReason.DIRECT_ACTUATOR_COMMAND.value,
        "Direct /cmd_vel reference; this layer only emits /cmd_vel_requested code.",
    ),
    (
        r"\b(?:disable|bypass)\s+(?:the\s+)?safety(?:\s+supervisor)?\b",
        SkillRejectionReason.SAFETY_OVERRIDE.value,
        "Attempt to disable or bypass safety supervisor.",
    ),
    (
        r"\bignore\s+safety\b",
        SkillRejectionReason.SAFETY_OVERRIDE.value,
        "Attempt to ignore safety supervisor.",
    ),
    (
        r"\b(?:ignore|override|disable)\s+(?:the\s+)?(?:e[-_ ]?stop|estop)\b",
        SkillRejectionReason.ESTOP_OVERRIDE.value,
        "Attempt to override e-stop.",
    ),
    (
        r"\b(?:forever|infinitely|indefinitely|unbounded)\b",
        SkillRejectionReason.UNBOUNDED_MOTION.value,
        "Unbounded motion request; every motion must be duration-bounded.",
    ),
    (
        r"\bas\s+fast\s+as\s+possible\b",
        SkillRejectionReason.UNBOUNDED_SPEED.value,
        "Unbounded speed request; speed must remain within safety limits.",
    ),
    (
        r"\b(?:max(?:imum)?|full)\s+speed\b",
        SkillRejectionReason.UNBOUNDED_SPEED.value,
        "Unbounded speed request; speed must remain within safety limits.",
    ),
    (
        r"\bspin\s+(?:the\s+)?motors?\b",
        SkillRejectionReason.DIRECT_MOTOR_CONTROL.value,
        "Direct motor control is out of scope; use /cmd_vel_requested only.",
    ),
    (
        r"\bmotor\s+controller\s+directly\b",
        SkillRejectionReason.DIRECT_MOTOR_CONTROL.value,
        "Direct motor controller access is out of scope.",
    ),
    (
        r"\b(?:disable|turn\s+off)\s+(?:the\s+)?lidar\b",
        SkillRejectionReason.SENSOR_DISABLE.value,
        "Attempt to disable lidar; sensors stay enabled.",
    ),
    (
        r"\b(?:shell|bash|sh)\s+command\b",
        SkillRejectionReason.SHELL_OR_CODE_EXECUTION.value,
        "Shell command requests are not supported.",
    ),
    (
        r"\brun\s+(?:shell|bash|sh)\b",
        SkillRejectionReason.SHELL_OR_CODE_EXECUTION.value,
        "Shell command execution is not supported.",
    ),
    (
        r"\bexecute\s+(?:python|code|script)\b",
        SkillRejectionReason.SHELL_OR_CODE_EXECUTION.value,
        "Arbitrary code execution is not supported.",
    ),
    (
        r"\bcurl\s+http",
        SkillRejectionReason.NETWORK_ACCESS.value,
        "Network egress is not supported in this layer.",
    ),
    (
        r"\bopen\s+(?:a\s+)?socket\b",
        SkillRejectionReason.NETWORK_ACCESS.value,
        "Network egress is not supported in this layer.",
    ),
)


# ---------------------------------------------------------------------
# Ambiguity rules.
# ---------------------------------------------------------------------

# Note: these run AFTER recognition, so "move forward 6 feet" is not
# ambiguous. They catch patterns that look like motion but supply no
# bounded parameter.
_AMBIGUOUS_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bgo\s+over\s+there\b", "destination is unspecified"),
    (r"\bgo\s+somewhere\b", "destination is unspecified"),
    (r"\bturn\s+a\s+little\b", "angle is unspecified"),
    (r"\bturn\s+slightly\b", "angle is unspecified"),
    (r"\bdrive\s+to\s+(?:that|the)\s+basket\b", "destination is not a known waypoint"),
)


# ---------------------------------------------------------------------
# Recognition rules. Each rule returns (skill_type, parameters,
# diagnostics) or None.
# ---------------------------------------------------------------------

_NUMBER = r"(\d+(?:\.\d+)?|\.\d+)"

_MOVE_FORWARD_FEET_RE_A = re.compile(
    rf"\b(?:move|drive|go)\s+(?:[a-z'_ ]+?\s+)?forward\s+{_NUMBER}\s*(?:ft|feet|foot)\b"
)
_MOVE_FORWARD_FEET_RE_B = re.compile(
    rf"\b(?:move|drive|go)\s+(?:[a-z'_ ]+?\s+)?{_NUMBER}\s*(?:ft|feet|foot)\s+forward\b"
)
_MOVE_FORWARD_METERS_RE_A = re.compile(
    rf"\b(?:move|drive|go)\s+(?:[a-z'_ ]+?\s+)?forward\s+{_NUMBER}\s*(?:m|meter|meters|metre|metres)\b"
)
_MOVE_FORWARD_METERS_RE_B = re.compile(
    rf"\b(?:move|drive|go)\s+(?:[a-z'_ ]+?\s+)?{_NUMBER}\s*(?:m|meter|meters|metre|metres)\s+forward\b"
)
_ROTATE_RE = re.compile(
    rf"\b(?:rotate|turn|spin)(?:\s+(left|right|clockwise|counter[-\s]?clockwise))?\s+{_NUMBER}\s*(?:deg|degrees|°)\b"
)
_STOP_RE = re.compile(r"\bstop\s+(?:immediately|now|the\s+robot|robot)\b")
_PUBLISH_REQUESTED_RE = re.compile(
    r"\bpublish\s+(?:a\s+)?requested(?:[-_\s]motion)?\b"
)
_KEYBOARD_RE = re.compile(
    r"\b(?:bind\s+)?(?:keyboard\s+key|key)\s+(?:to\s+)?(?:move|drive|go)\s+(?:forward|fwd)\b"
)
_KEYBOARD_NAMED_RE = re.compile(
    r"\b(?:keyboard\s+)?key\s+(?:'|\")?(?P<key>[a-z0-9])(?:'|\")?\s+(?:to\s+)?(?:move|drive|go)\s+(?:forward|fwd)\b"
)
_CONTROLLER_RE = re.compile(
    r"\bcontroller\s+button\s+(?:to\s+)?(?P<verb>stop|move|drive)\b"
)
_WAYPOINT_RE = re.compile(
    r"\bgo\s+to\s+waypoint\s+(?P<name>[a-z0-9_]+)\b"
)
_PATROL_RE = re.compile(
    r"\bpatrol\s+(?P<list>[a-z0-9_]+(?:\s+[a-z0-9_]+){1,7})\b"
)
_SAFE_STOP_WRAPPER_RE = re.compile(
    r"\bwrap\s+(?:[a-z_]+\s+)?in\s+safe[-\s]?stop\b"
)


def _try_move_forward(normalised: str) -> Optional[tuple[str, tuple[SkillParameter, ...], tuple[SkillDiagnostic, ...]]]:
    for pattern in (_MOVE_FORWARD_FEET_RE_A, _MOVE_FORWARD_FEET_RE_B):
        match = pattern.search(normalised)
        if match:
            feet = float(match.group(1))
            meters = round(feet * _FEET_TO_METERS, 4)
            return (
                SkillType.MOVE_FORWARD_DISTANCE.value,
                (
                    SkillParameter(name="distance_meters", value=meters, units="m"),
                    SkillParameter(name="source_distance", value=feet, units="ft"),
                ),
                (
                    info(
                        "request_accepted",
                        f"converted {feet} feet to {meters} meters",
                        parameter="distance_meters",
                    ),
                ),
            )

    for pattern in (_MOVE_FORWARD_METERS_RE_A, _MOVE_FORWARD_METERS_RE_B):
        match = pattern.search(normalised)
        if match:
            meters = float(match.group(1))
            return (
                SkillType.MOVE_FORWARD_DISTANCE.value,
                (
                    SkillParameter(name="distance_meters", value=meters, units="m"),
                    SkillParameter(name="source_distance", value=meters, units="m"),
                ),
                (info("request_accepted", "distance specified in meters"),),
            )
    return None


def _try_rotate(normalised: str) -> Optional[tuple[str, tuple[SkillParameter, ...], tuple[SkillDiagnostic, ...]]]:
    match = _ROTATE_RE.search(normalised)
    if match is None:
        return None
    direction_token = match.group(1) or "left"
    if direction_token in {"left", "counter-clockwise", "counter clockwise", "counterclockwise"}:
        direction = "left"
    elif direction_token in {"right", "clockwise"}:
        direction = "right"
    else:
        direction = "left"
    degrees = float(match.group(2))
    return (
        SkillType.ROTATE_DEGREES.value,
        (
            SkillParameter(name="angle_degrees", value=degrees, units="deg"),
            SkillParameter(name="direction", value=direction, units=""),
        ),
        (info("request_accepted", f"rotate {direction} {degrees} degrees"),),
    )


def _try_stop(normalised: str) -> Optional[tuple[str, tuple[SkillParameter, ...], tuple[SkillDiagnostic, ...]]]:
    if _STOP_RE.search(normalised):
        return (
            SkillType.STOP_IMMEDIATELY.value,
            (),
            (info("request_accepted", "stop request recognised"),),
        )
    return None


def _try_publish_requested(normalised: str) -> Optional[tuple[str, tuple[SkillParameter, ...], tuple[SkillDiagnostic, ...]]]:
    if not _PUBLISH_REQUESTED_RE.search(normalised):
        return None
    # Defaults — the caller can override via the request parameters in
    # the future; the parser does not invent values.
    return (
        SkillType.PUBLISH_REQUESTED_MOTION.value,
        (
            SkillParameter(name="linear_x_mps", value=0.2, units="m/s"),
            SkillParameter(name="angular_z_rad_s", value=0.0, units="rad/s"),
        ),
        (info("request_accepted", "single requested-motion publication"),),
    )


def _try_keyboard(normalised: str) -> Optional[tuple[str, tuple[SkillParameter, ...], tuple[SkillDiagnostic, ...]]]:
    named = _KEYBOARD_NAMED_RE.search(normalised)
    if named:
        key = named.group("key")
        return (
            SkillType.KEYBOARD_FORWARD_BINDING.value,
            (SkillParameter(name="key", value=key, units=""),),
            (info("request_accepted", f"keyboard key '{key}' bound to forward motion"),),
        )
    if _KEYBOARD_RE.search(normalised):
        return (
            SkillType.KEYBOARD_FORWARD_BINDING.value,
            (SkillParameter(name="key", value="w", units=""),),
            (info("request_accepted", "keyboard key 'w' bound to forward motion (default)"),),
        )
    return None


def _try_controller(normalised: str) -> Optional[tuple[str, tuple[SkillParameter, ...], tuple[SkillDiagnostic, ...]]]:
    match = _CONTROLLER_RE.search(normalised)
    if match is None:
        return None
    verb = match.group("verb")
    button = "a" if verb == "stop" else "rb"
    return (
        SkillType.CONTROLLER_BUTTON_BINDING.value,
        (
            SkillParameter(name="button", value=button, units=""),
            SkillParameter(name="verb", value=verb, units=""),
        ),
        (info("request_accepted", f"controller button '{button}' bound to {verb}"),),
    )


def _try_waypoint(normalised: str) -> Optional[tuple[str, tuple[SkillParameter, ...], tuple[SkillDiagnostic, ...]]]:
    match = _WAYPOINT_RE.search(normalised)
    if match is None:
        return None
    name = match.group("name")
    return (
        SkillType.WAYPOINT_REQUEST.value,
        (SkillParameter(name="waypoint_id", value=name, units=""),),
        (info("request_accepted", f"waypoint '{name}' request"),),
    )


def _try_patrol(normalised: str) -> Optional[tuple[str, tuple[SkillParameter, ...], tuple[SkillDiagnostic, ...]]]:
    match = _PATROL_RE.search(normalised)
    if match is None:
        return None
    waypoints = match.group("list").split()
    return (
        SkillType.PATROL_ROUTE_TEMPLATE.value,
        (SkillParameter(name="waypoints", value=tuple(waypoints), units=""),),
        (
            info(
                "request_accepted",
                f"patrol route with {len(waypoints)} named waypoints",
            ),
        ),
    )


def _try_safe_stop_wrapper(normalised: str) -> Optional[tuple[str, tuple[SkillParameter, ...], tuple[SkillDiagnostic, ...]]]:
    if _SAFE_STOP_WRAPPER_RE.search(normalised):
        return (
            SkillType.SAFE_STOP_WRAPPER.value,
            (),
            (info("request_accepted", "safe-stop wrapper requested"),),
        )
    return None


_RECOGNISERS: tuple = (
    _try_move_forward,
    _try_rotate,
    _try_stop,
    _try_publish_requested,
    _try_keyboard,
    _try_controller,
    _try_waypoint,
    _try_patrol,
    _try_safe_stop_wrapper,
)


def parse_request(text: str) -> SkillCandidate:
    """Parse a developer request and return a :class:`SkillCandidate`.

    The function never raises; on bad input it returns a candidate
    with status ``rejected`` / ``ambiguous`` / ``unsupported`` and
    diagnostics that explain why.
    """

    if not isinstance(text, str) or not text.strip():
        return SkillCandidate(
            skill_type=None,
            parameters=(),
            diagnostics=(
                rejection("ambiguous_request", "empty request text"),
            ),
            status=SkillGenerationStatus.AMBIGUOUS.value,
            rejection_reason=SkillRejectionReason.AMBIGUOUS_REQUEST.value,
            normalised_text="",
        )

    normalised = _normalise(text)

    # 1) Rejection rules first.
    rejection_diags: list[SkillDiagnostic] = []
    first_reason: str = ""
    for pattern, reason, message in _REJECTION_RULES:
        if re.search(pattern, normalised):
            rejection_diags.append(rejection(reason, message))
            if not first_reason:
                first_reason = reason
    if rejection_diags:
        return SkillCandidate(
            skill_type=None,
            parameters=(),
            diagnostics=tuple(rejection_diags),
            status=SkillGenerationStatus.REJECTED.value,
            rejection_reason=first_reason,
            normalised_text=normalised,
        )

    # 2) Ambiguity (run before recognition so "go over there" never
    # matches "go to waypoint").
    for pattern, message in _AMBIGUOUS_PATTERNS:
        if re.search(pattern, normalised):
            return SkillCandidate(
                skill_type=None,
                parameters=(),
                diagnostics=(
                    rejection("ambiguous_request", message),
                ),
                status=SkillGenerationStatus.AMBIGUOUS.value,
                rejection_reason=SkillRejectionReason.AMBIGUOUS_REQUEST.value,
                normalised_text=normalised,
            )

    # 3) Recognition.
    for recogniser in _RECOGNISERS:
        result = recogniser(normalised)
        if result is None:
            continue
        skill_type, params, diagnostics = result
        # Bounds-check parameters: distance / angle.
        bounds_diags = _check_bounds(skill_type, params)
        if bounds_diags:
            return SkillCandidate(
                skill_type=skill_type,
                parameters=params,
                diagnostics=tuple(diagnostics) + tuple(bounds_diags),
                status=SkillGenerationStatus.REJECTED.value,
                rejection_reason=SkillRejectionReason.OUT_OF_RANGE_PARAMETER.value,
                normalised_text=normalised,
            )
        return SkillCandidate(
            skill_type=skill_type,
            parameters=params,
            diagnostics=tuple(diagnostics),
            status=SkillGenerationStatus.GENERATED.value,
            normalised_text=normalised,
        )

    # 4) Generic "move forward" without a number => ambiguous.
    if re.search(r"\b(?:move|drive|go)\s+forward\b", normalised):
        return SkillCandidate(
            skill_type=None,
            parameters=(),
            diagnostics=(
                rejection(
                    "ambiguous_request",
                    "forward distance is unspecified; please give a distance with units",
                ),
            ),
            status=SkillGenerationStatus.AMBIGUOUS.value,
            rejection_reason=SkillRejectionReason.AMBIGUOUS_REQUEST.value,
            normalised_text=normalised,
        )

    # 5) Fall-through: unsupported.
    return SkillCandidate(
        skill_type=None,
        parameters=(),
        diagnostics=(
            rejection(
                "unsupported_instruction",
                "no supported skill template matched this request",
            ),
        ),
        status=SkillGenerationStatus.UNSUPPORTED.value,
        rejection_reason=SkillRejectionReason.UNSUPPORTED_INSTRUCTION.value,
        normalised_text=normalised,
    )


def _check_bounds(
    skill_type: str, params: tuple[SkillParameter, ...]
) -> tuple[SkillDiagnostic, ...]:
    out: list[SkillDiagnostic] = []
    for param in params:
        if (
            skill_type == SkillType.MOVE_FORWARD_DISTANCE.value
            and param.name == "distance_meters"
        ):
            try:
                value = float(param.value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                out.append(
                    rejection(
                        "out_of_range_parameter",
                        f"distance_meters is not numeric: {param.value!r}",
                        parameter=param.name,
                    )
                )
                continue
            if value <= 0:
                out.append(
                    rejection(
                        "out_of_range_parameter",
                        "distance must be positive",
                        parameter=param.name,
                    )
                )
            if value > _MAX_DISTANCE_M:
                out.append(
                    rejection(
                        "out_of_range_parameter",
                        f"distance must be <= {_MAX_DISTANCE_M} m",
                        parameter=param.name,
                    )
                )
        if (
            skill_type == SkillType.ROTATE_DEGREES.value
            and param.name == "angle_degrees"
        ):
            try:
                value = abs(float(param.value))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                out.append(
                    rejection(
                        "out_of_range_parameter",
                        f"angle_degrees is not numeric: {param.value!r}",
                        parameter=param.name,
                    )
                )
                continue
            if value <= 0:
                out.append(
                    rejection(
                        "out_of_range_parameter",
                        "angle must be positive",
                        parameter=param.name,
                    )
                )
            if value > _MAX_ANGLE_DEG:
                out.append(
                    rejection(
                        "out_of_range_parameter",
                        f"|angle| must be <= {_MAX_ANGLE_DEG} degrees",
                        parameter=param.name,
                    )
                )
    return tuple(out)


def feet_to_meters(feet: float) -> float:
    """Public helper. Used by tests."""

    return round(feet * _FEET_TO_METERS, 4)
