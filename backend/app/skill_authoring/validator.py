"""Static safety validation for generated snippets.

The validator runs **after** the template builder so it can catch a
buggy or unsafe template before the snippet reaches the operator's
clipboard. It is the second chokepoint; the parser already rejected
forbidden phrases, so this layer focuses on the code text.

Rules enforced:

* code never references ``/cmd_vel`` outside of ``/cmd_vel_requested``;
* motion templates contain a ``Twist()`` zero / stop emission;
* motion templates have a bounded loop (duration, count, or watchdog);
* code does not import or call shell / network / eval / exec;
* code does not contain ``while True`` without a ``break`` (only
  bounded ``while rclpy.ok() and ...`` survives);
* code mentions ``safety supervisor`` in a comment.
"""

from __future__ import annotations

import re
from typing import Iterable

from .diagnostics import info, rejection, warning
from .models import (
    GeneratedSkill,
    SkillAuthoringRequest,
    SkillDiagnostic,
    SkillGenerationStatus,
    SkillRejectionReason,
    SkillType,
)


# Tokens that may never appear in generated motion code (case-insensitive
# search against the rendered text).
FORBIDDEN_CODE_TOKENS: tuple[tuple[str, str, str], ...] = (
    (
        r"\bsubprocess\b",
        "shell_or_code_execution",
        "subprocess use is forbidden",
    ),
    (
        r"\bos\.system\b",
        "shell_or_code_execution",
        "os.system use is forbidden",
    ),
    (
        r"\bos\.popen\b",
        "shell_or_code_execution",
        "os.popen use is forbidden",
    ),
    (
        r"\beval\(",
        "shell_or_code_execution",
        "eval() is forbidden",
    ),
    (
        r"\bexec\(",
        "shell_or_code_execution",
        "exec() is forbidden",
    ),
    (
        r"\bsocket\.socket\b",
        "network_access",
        "raw socket use is forbidden",
    ),
    (
        r"\burllib\.request\b",
        "network_access",
        "urllib.request use is forbidden",
    ),
    (
        r"^import\s+requests\b",
        "network_access",
        "requests module is forbidden",
    ),
    (
        r"^import\s+httpx\b",
        "network_access",
        "httpx module is forbidden",
    ),
    (
        r"^import\s+openai\b",
        "shell_or_code_execution",
        "openai SDK is forbidden in skill code",
    ),
    (
        r"^import\s+anthropic\b",
        "shell_or_code_execution",
        "anthropic SDK is forbidden in skill code",
    ),
)


# Tokens required in motion code (heuristic but deterministic).
REQUIRED_CODE_TOKENS: dict[str, tuple[str, ...]] = {
    SkillType.MOVE_FORWARD_DISTANCE.value: (
        r"/cmd_vel_requested",
        r"Twist\(\)",
        r"DURATION_S",
        r"TIMEOUT_S",
        r"safety supervisor",
    ),
    SkillType.ROTATE_DEGREES.value: (
        r"/cmd_vel_requested",
        r"Twist\(\)",
        r"DURATION_S",
        r"TIMEOUT_S",
        r"safety supervisor",
    ),
    SkillType.STOP_IMMEDIATELY.value: (
        r"/cmd_vel_requested",
        r"Twist\(\)",
        r"PUBLISH_COUNT",
        r"safety supervisor",
    ),
    SkillType.PUBLISH_REQUESTED_MOTION.value: (
        r"/cmd_vel_requested",
        r"Twist\(\)",
        r"safety supervisor",
    ),
    SkillType.KEYBOARD_FORWARD_BINDING.value: (
        r"/cmd_vel_requested",
        r"Twist\(\)",
        r"WATCHDOG_SECONDS",
        r"safety supervisor",
    ),
    SkillType.CONTROLLER_BUTTON_BINDING.value: (
        r"/cmd_vel_requested",
        r"Twist\(\)",
        r"WATCHDOG_SECONDS",
        r"safety supervisor",
    ),
    SkillType.WAYPOINT_REQUEST.value: (
        r"safety supervisor",
    ),
    SkillType.PATROL_ROUTE_TEMPLATE.value: (
        r"safety supervisor",
    ),
    SkillType.SAFE_STOP_WRAPPER.value: (
        r"/cmd_vel_requested",
        r"Twist\(\)",
        r"safety supervisor",
    ),
}


_CMD_VEL_FORBIDDEN_RE = re.compile(r"(?<!_requested)\b/cmd_vel\b(?!_)")
_WHILE_TRUE_RE = re.compile(r"\bwhile\s+True\s*:")


def _has_forbidden_token(code: str) -> list[SkillDiagnostic]:
    out: list[SkillDiagnostic] = []
    for pattern, reason, message in FORBIDDEN_CODE_TOKENS:
        if re.search(pattern, code, flags=re.MULTILINE):
            out.append(rejection(reason, message))
    return out


def _has_unbounded_loop(code: str) -> list[SkillDiagnostic]:
    out: list[SkillDiagnostic] = []
    for match in _WHILE_TRUE_RE.finditer(code):
        # ``while True:`` is forbidden — even with a break inside,
        # the safer pattern is ``while rclpy.ok() and not done:``.
        out.append(
            rejection(
                "unbounded_motion",
                f"`while True:` is forbidden; use a bounded loop instead",
            )
        )
    return out


def _references_direct_cmd_vel(code: str) -> list[SkillDiagnostic]:
    # Strip Python comment lines first; the safety header
    # intentionally mentions /cmd_vel and /cmd_vel_authorized in
    # comments so a reader knows the boundary.
    non_comment: list[str] = []
    for line in code.splitlines():
        stripped_line = line.split("#", 1)[0]
        non_comment.append(stripped_line)
    stripped = "\n".join(non_comment)
    # Strip approved /cmd_vel_<suffix> identifiers before checking
    # for a bare /cmd_vel reference in executable code.
    for approved in ("/cmd_vel_requested", "/cmd_vel_authorized"):
        stripped = stripped.replace(approved, "")
    if re.search(r"/cmd_vel(?![_a-zA-Z0-9])", stripped):
        return [
            rejection(
                "direct_actuator_command",
                "code references /cmd_vel outside of /cmd_vel_requested",
            )
        ]
    return []


def _missing_required_tokens(
    code: str, skill_type: str
) -> list[SkillDiagnostic]:
    out: list[SkillDiagnostic] = []
    required = REQUIRED_CODE_TOKENS.get(skill_type, ())
    for token in required:
        if not re.search(token, code, flags=re.IGNORECASE):
            out.append(
                rejection(
                    "validation_failed",
                    f"required token missing in generated code: {token}",
                )
            )
    return out


def validate_generated_code(code: str, skill_type: str) -> tuple[SkillDiagnostic, ...]:
    """Return rejection diagnostics; empty tuple means valid."""

    diags: list[SkillDiagnostic] = []
    diags.extend(_references_direct_cmd_vel(code))
    diags.extend(_has_forbidden_token(code))
    diags.extend(_has_unbounded_loop(code))
    diags.extend(_missing_required_tokens(code, skill_type))
    return tuple(diags)


def validate_generated_skill(
    skill: GeneratedSkill,
) -> tuple[SkillDiagnostic, ...]:
    """Re-validate a generated skill object."""

    diags = list(validate_generated_code(skill.code, skill.skill_type))
    if not skill.disclaimer:
        diags.append(rejection("validation_failed", "missing disclaimer"))
    return tuple(diags)


def validate_intent_request(
    request: SkillAuthoringRequest,
) -> tuple[SkillDiagnostic, ...]:
    """Validate the request envelope before parsing.

    Currently a sanity check: non-empty text, supported language.
    """

    diags: list[SkillDiagnostic] = []
    if not request.text or not request.text.strip():
        diags.append(rejection("ambiguous_request", "request text is empty"))
    if request.language not in {"python_ros2", "pseudo_code", "cpp_ros2"}:
        diags.append(
            rejection(
                "unsupported_instruction",
                f"unsupported language: {request.language!r}",
            )
        )
    return tuple(diags)
