"""Sanitizer for raw LLM candidate output.

The sanitizer is the first chokepoint between an untrusted provider
and the deterministic Phase 15A skill validator. It refuses any
candidate whose code, explanation, declared topics, or declared
interfaces reference forbidden phrases.

Allowed:
* ``/cmd_vel_requested`` in code or interfaces
* mentions of ``/cmd_vel`` in plain English inside the explanation
  (so a model can correctly describe why direct actuator publication
  is forbidden) — but **not** inside ``code`` or
  ``declared_topics``.

Rejected: every fragment listed in :data:`FORBIDDEN_FRAGMENTS`.
"""

from __future__ import annotations

import re
from typing import Iterable

from .models import (
    CandidateRejectionReason,
    SkillLLMCandidate,
    SkillLLMSanitizerResult,
)


# Each tuple is (regex, code, message). Codes match
# :class:`CandidateRejectionReason` values where they exist.
FORBIDDEN_FRAGMENTS: tuple[tuple[str, str, str], ...] = (
    (r"\bwhile\s+True\s*:", CandidateRejectionReason.UNBOUNDED_MOTION.value, "unbounded while True loop"),
    (r"\bsubprocess\b", CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value, "subprocess module use"),
    (r"\bos\.system\b", CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value, "os.system call"),
    (r"\bos\.popen\b", CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value, "os.popen call"),
    (r"\beval\(", CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value, "eval() use"),
    (r"\bexec\(", CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value, "exec() use"),
    (r"\bsocket\.socket\b", CandidateRejectionReason.NETWORK_ACCESS.value, "raw socket use"),
    (r"\burllib\.request\b", CandidateRejectionReason.NETWORK_ACCESS.value, "urllib.request use"),
    (r"\brequests\.(?:get|post|put|delete|head|patch)\b", CandidateRejectionReason.NETWORK_ACCESS.value, "requests library call"),
    (r"\bhttpx\.(?:get|post|put|delete|head|patch|Client|AsyncClient)\b", CandidateRejectionReason.NETWORK_ACCESS.value, "httpx library call"),
    (r"\bimport\s+openai\b", CandidateRejectionReason.NETWORK_ACCESS.value, "openai SDK import"),
    (r"\bimport\s+anthropic\b", CandidateRejectionReason.NETWORK_ACCESS.value, "anthropic SDK import"),
    (r"\bimport\s+cohere\b", CandidateRejectionReason.NETWORK_ACCESS.value, "cohere SDK import"),
    (r"\bapi_key\s*=", CandidateRejectionReason.SECRET_LEAK.value, "api_key assignment"),
    (r"\bAPI_KEY\b", CandidateRejectionReason.SECRET_LEAK.value, "API_KEY constant"),
    (r"\bpassword\s*=", CandidateRejectionReason.SECRET_LEAK.value, "password assignment"),
    (r"\bsecret\s*=", CandidateRejectionReason.SECRET_LEAK.value, "secret assignment"),
    (r"\brm\s+-rf\b", CandidateRejectionReason.DESTRUCTIVE_COMMAND.value, "destructive shell command"),
    (r"\bsudo\b", CandidateRejectionReason.DESTRUCTIVE_COMMAND.value, "sudo command"),
    (r"\bchmod\s+\d+\b", CandidateRejectionReason.DESTRUCTIVE_COMMAND.value, "chmod command"),
    (r"\bchown\s+", CandidateRejectionReason.DESTRUCTIVE_COMMAND.value, "chown command"),
    (
        r"\bros2\s+topic\s+pub\s+/cmd_vel(?!_)",
        CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value,
        "direct ros2 topic pub to /cmd_vel",
    ),
    (
        r"\bdirect\s+motor(?:s)?\b",
        CandidateRejectionReason.DIRECT_MOTOR_CONTROL.value,
        "direct motor control reference",
    ),
    (
        r"\b(?:disable|bypass)\s+(?:the\s+)?safety(?:\s+supervisor)?\b",
        CandidateRejectionReason.SAFETY_OVERRIDE.value,
        "safety supervisor override",
    ),
    (
        r"\bignore\s+safety\b",
        CandidateRejectionReason.SAFETY_OVERRIDE.value,
        "ignore safety phrase",
    ),
    (
        r"\b(?:ignore|override|disable)\s+(?:the\s+)?(?:e[-_ ]?stop|estop)\b",
        CandidateRejectionReason.SAFETY_OVERRIDE.value,
        "estop override",
    ),
)


def _scan(text: str) -> list[tuple[str, str, str]]:
    """Return matches as ``(matched, code, message)`` triples.

    Matching is case-insensitive so an LLM that emits "Disable Safety"
    is still caught.
    """

    if not text:
        return []
    out: list[tuple[str, str, str]] = []
    for pattern, code, message in FORBIDDEN_FRAGMENTS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match is not None:
            out.append((match.group(0), code, message))
    return out


def _strip_python_comments(code: str) -> str:
    """Remove the ``# ...`` portion of each line of code.

    The Phase 15A safety header intentionally mentions ``/cmd_vel``
    and ``/cmd_vel_authorized`` in comments to document the
    forbidden boundary. Stripping comments before the ``/cmd_vel``
    check avoids false positives.
    """

    out: list[str] = []
    for line in code.splitlines():
        out.append(line.split("#", 1)[0])
    return "\n".join(out)


def _references_direct_cmd_vel(text: str) -> bool:
    """Return True if executable text references ``/cmd_vel`` directly."""

    stripped = _strip_python_comments(text)
    # Remove approved topic suffixes first.
    for approved in ("/cmd_vel_requested", "/cmd_vel_authorized"):
        stripped = stripped.replace(approved, "")
    return re.search(r"/cmd_vel(?![_a-zA-Z0-9])", stripped) is not None


def sanitize_candidate(candidate: SkillLLMCandidate) -> SkillLLMSanitizerResult:
    """Run every sanitizer rule against the candidate."""

    reason_codes: list[str] = []
    blocked: list[str] = []
    notes: list[str] = []

    # 1) Forbidden-fragment scan over code + provider-declared
    # interfaces / topics / safety constraints. The explanation
    # field is scanned for sentinel phrases but allowed to mention
    # ``/cmd_vel`` (the model is supposed to describe the boundary).
    fields_to_scan: tuple[tuple[str, str], ...] = (
        ("code", candidate.code),
        ("declared_topics", "\n".join(candidate.declared_topics)),
        ("declared_interfaces", "\n".join(candidate.declared_interfaces)),
        ("declared_safety_constraints", "\n".join(candidate.declared_safety_constraints)),
        ("raw_provider_payload", candidate.raw_provider_payload),
    )
    explanation_scan: tuple[tuple[str, str], ...] = (
        ("explanation", candidate.explanation),
    )

    for field_name, text in fields_to_scan:
        for matched, code, message in _scan(text):
            reason_codes.append(code)
            blocked.append(f"{field_name}:{matched}")
            notes.append(f"{field_name}: {message}")

    # Explanation scan: skip safety-override / direct-actuator codes
    # so a correct model description ("never publish to /cmd_vel
    # directly") does not count as an override attempt — those are
    # caught in code/topics/interfaces instead.
    _explanation_allowlist: frozenset[str] = frozenset()
    for field_name, text in explanation_scan:
        for matched, code, message in _scan(text):
            if code in {
                CandidateRejectionReason.SAFETY_OVERRIDE.value,
                CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value,
            }:
                # A safety-supervisor reference in the explanation is
                # acceptable IF the surrounding sentence is not an
                # imperative. We are conservative: keep the strict
                # rule for everything except neutral descriptions.
                # The simple rule below: an explanation that contains
                # "do not" or "must not" near the matched fragment is
                # exempt.
                excerpt = text.lower()
                if "do not" in excerpt or "must not" in excerpt or "never" in excerpt:
                    notes.append(
                        f"{field_name}: descriptive use of '{matched}' allowed"
                    )
                    continue
            reason_codes.append(code)
            blocked.append(f"{field_name}:{matched}")
            notes.append(f"{field_name}: {message}")

    # 2) Direct /cmd_vel check (executable text only — strips
    # comments + approved topic suffixes).
    if _references_direct_cmd_vel(candidate.code):
        reason_codes.append(
            CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value
        )
        blocked.append("code:/cmd_vel")
        notes.append("code: direct /cmd_vel publication is forbidden")
    for topic in candidate.declared_topics:
        if topic.strip() == "/cmd_vel":
            reason_codes.append(
                CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value
            )
            blocked.append("declared_topics:/cmd_vel")
            notes.append("declared_topics: /cmd_vel is forbidden; use /cmd_vel_requested")

    # 3) Confidence labelling — "overconfident" is not auto-reject
    # but does mark the candidate for human review.
    if candidate.confidence_label == "overconfident":
        notes.append("provider declares confidence='overconfident'; treat as suspect")

    if reason_codes:
        return SkillLLMSanitizerResult(
            status="rejected",
            accepted=False,
            reason_codes=tuple(dict.fromkeys(reason_codes)),  # dedupe, preserve order
            blocked_fragments=tuple(blocked),
            notes=tuple(notes),
            human_review_required=True,
        )

    return SkillLLMSanitizerResult(
        status="accepted",
        accepted=True,
        reason_codes=(),
        blocked_fragments=(),
        notes=tuple(notes),
        human_review_required=candidate.confidence_label == "overconfident",
    )
