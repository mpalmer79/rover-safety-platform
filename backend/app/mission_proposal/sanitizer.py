"""Proposal sanitizer.

The sanitizer is the boundary between an untrusted proposal and the
deterministic mission compiler. It rejects proposals that try to
bypass safety authority or run unsupported / dangerous behaviour.

The rules are intentionally narrow and deterministic. A future LLM
proposal that uses a phrase listed in :data:`FORBIDDEN_PHRASES` is
rejected before the compiler even sees it; the compiler then never
has to interpret unsafe text.
"""

from __future__ import annotations

import re
from typing import Iterable

from .models import (
    MissionProposal,
    SANITIZER_STATUS_ACCEPTED,
    SANITIZER_STATUS_REJECTED,
    SanitizerDiagnostic,
    SanitizerResult,
)


# Forbidden phrases. Each tuple is (matcher, code, message). The
# matcher is a regex applied to the *normalised* (lowercased + simple
# whitespace) form of the candidate text. The ordering is significant
# only for human-readable output; the sanitizer evaluates every rule
# regardless and records every match.
FORBIDDEN_PHRASES: tuple[tuple[str, str, str], ...] = (
    (r"\bcmd_vel\b", "direct_actuator_command", "Direct actuator command referenced"),
    (r"\b/cmd_vel\b", "direct_actuator_command", "Direct actuator topic referenced"),
    (r"\bignore\s+safety\b", "safety_override", "Attempt to ignore safety supervisor"),
    (r"\bdisable\s+safety\b", "safety_override", "Attempt to disable safety supervisor"),
    (
        r"\bdisable\s+safety\s+supervisor\b",
        "safety_override",
        "Attempt to disable safety supervisor",
    ),
    (
        r"\boverride\s+(?:the\s+)?(?:e[-_ ]?stop|estop)\b",
        "estop_override",
        "Attempt to override e-stop",
    ),
    (
        r"\bdisable\s+(?:the\s+)?lidar\b",
        "sensor_disable",
        "Attempt to disable lidar",
    ),
    (
        r"\bcontinue\s+despite\s+sensor\s+failure\b",
        "continue_despite_failure",
        "Attempt to continue under sensor failure",
    ),
    (
        r"\bshell\s+command\b",
        "shell_command",
        "Shell command referenced",
    ),
    (
        r"\brun\s+(?:shell|bash|sh)\b",
        "shell_command",
        "Shell execution requested",
    ),
    (
        r"\bcode\s+execution\b",
        "code_execution",
        "Code execution requested",
    ),
    (
        r"\bexecute\s+(?:python|code|script)\b",
        "code_execution",
        "Script execution requested",
    ),
    (
        r"\bnetwork\s+command\b",
        "network_command",
        "Network command requested",
    ),
    (
        r"\bcurl\s+http",
        "network_command",
        "HTTP request requested",
    ),
    (
        r"\brm\s+-rf\b",
        "destructive_command",
        "Destructive shell command referenced",
    ),
    (
        r"\bunknown\s+location\b",
        "unknown_location_self_declared",
        "Proposal self-declares an unknown location",
    ),
    (
        r"\bunsupported\s+intent\b",
        "unsupported_intent_self_declared",
        "Proposal self-declares an unsupported intent",
    ),
)


_WHITESPACE_RE = re.compile(r"\s+")


def _normalise(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.lower()).strip()


def _candidate_corpus(proposal: MissionProposal) -> tuple[str, ...]:
    """Strings the sanitizer scans for forbidden content.

    The proposal's raw_response is included so a malicious provider
    cannot hide unsafe intent inside the free-form field.
    """

    return (
        proposal.proposed_intent,
        proposal.proposed_location,
        proposal.proposed_motion_style,
        " ".join(proposal.proposed_constraints),
        proposal.proposed_recovery_policy,
        proposal.raw_response,
    )


def sanitize_proposal(proposal: MissionProposal) -> SanitizerResult:
    """Run every rule against the proposal and return a result."""

    corpus = " || ".join(_candidate_corpus(proposal))
    haystack = _normalise(corpus)

    diagnostics: list[SanitizerDiagnostic] = []
    blocked: list[str] = []

    for pattern, code, message in FORBIDDEN_PHRASES:
        match = re.search(pattern, haystack)
        if match is None:
            continue
        diagnostics.append(
            SanitizerDiagnostic(
                code=code,
                severity="rejection",
                message=message,
                matched_phrase=match.group(0),
            )
        )
        blocked.append(match.group(0))

    notes: list[str] = []
    if proposal.confidence_label == "overconfident":
        notes.append(
            "provider self-labels confidence='overconfident'; treat as suspect"
        )

    if diagnostics:
        return SanitizerResult(
            status=SANITIZER_STATUS_REJECTED,
            accepted=False,
            sanitized_intent="",
            blocked_phrases=tuple(blocked),
            diagnostics=tuple(diagnostics),
            notes=tuple(notes),
        )

    # Build sanitized intent text. It is the catenation of the
    # proposal's intent-bearing fields, in a stable order, with a
    # final "return to dock" hint if the recovery policy says so.
    pieces: list[str] = []
    if proposal.proposed_intent.strip():
        pieces.append(proposal.proposed_intent.strip().rstrip("."))
    if proposal.proposed_constraints:
        for constraint in proposal.proposed_constraints:
            if constraint.strip():
                pieces.append(constraint.strip().rstrip("."))
    if proposal.proposed_recovery_policy.strip():
        pieces.append(proposal.proposed_recovery_policy.strip().rstrip("."))

    sanitized = ". ".join(pieces) + ("." if pieces else "")

    return SanitizerResult(
        status=SANITIZER_STATUS_ACCEPTED,
        accepted=True,
        sanitized_intent=sanitized,
        blocked_phrases=(),
        diagnostics=(),
        notes=tuple(notes),
    )
