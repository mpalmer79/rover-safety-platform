"""Deterministic candidate ranking.

Multiple candidates can be returned by a single provider invocation.
The ranker scores each one with a fully deterministic signal set —
sanitizer outcome, validator outcome, presence of stop / timeout,
absence of forbidden imports, etc. Model confidence is metadata
only; the validator outcome dominates.

The ranker is intentionally simple. No ML, no heuristics derived
from model output. Every contribution is documented + tested.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .models import (
    CandidateConfidence,
    SkillLLMCandidate,
    SkillLLMSanitizerResult,
    SkillLLMValidationResult,
)


# Each signal returns an integer "delta" against the candidate's
# running total. The validator outcome dominates: a validator-
# accepted candidate scores at least +50; a rejection scores -100.
SCORE_VALIDATOR_ACCEPTED: int = 50
SCORE_VALIDATOR_REJECTED: int = -100
SCORE_SANITIZER_REJECTED: int = -200
SCORE_HAS_STOP_COMMAND: int = 10
SCORE_HAS_TIMEOUT: int = 10
SCORE_USES_CMD_VEL_REQUESTED: int = 8
SCORE_FORBIDDEN_IMPORT: int = -50
SCORE_BOUNDED_SPEED: int = 6
SCORE_BOUNDED_DISTANCE: int = 6
SCORE_EXPLANATION_PROVIDED: int = 4
SCORE_DISCLOSED_UNCERTAINTY: int = 3
SCORE_OVERCONFIDENT_WITHOUT_VALIDATION: int = -25


FORBIDDEN_IMPORT_HINTS: tuple[str, ...] = (
    "import os",
    "import subprocess",
    "import socket",
    "import requests",
    "from os ",
    "from socket ",
    "open(\"/etc/",
)


@dataclass(frozen=True)
class CandidateScoreBreakdown:
    """Per-signal contribution to a candidate's score."""

    signal: str
    delta: int
    note: str = ""


@dataclass(frozen=True)
class CandidateRanking:
    candidate_id: str
    rank: int
    score: int
    accepted: bool
    safety_status: str
    breakdown: tuple[CandidateScoreBreakdown, ...] = ()


def _score_candidate(
    candidate: SkillLLMCandidate,
    sanitizer: SkillLLMSanitizerResult,
    validator: SkillLLMValidationResult,
) -> tuple[int, list[CandidateScoreBreakdown]]:
    breakdown: list[CandidateScoreBreakdown] = []
    score = 0

    # Validator + sanitizer dominate.
    if not sanitizer.accepted:
        score += SCORE_SANITIZER_REJECTED
        breakdown.append(
            CandidateScoreBreakdown(
                signal="sanitizer_rejected",
                delta=SCORE_SANITIZER_REJECTED,
                note="sanitizer refused candidate",
            )
        )
    if validator.invoked:
        if validator.accepted:
            score += SCORE_VALIDATOR_ACCEPTED
            breakdown.append(
                CandidateScoreBreakdown(
                    "validator_accepted", SCORE_VALIDATOR_ACCEPTED
                )
            )
        else:
            score += SCORE_VALIDATOR_REJECTED
            breakdown.append(
                CandidateScoreBreakdown(
                    "validator_rejected", SCORE_VALIDATOR_REJECTED
                )
            )

    code = candidate.code or ""
    code_lower = code.lower()

    if "twist()" in code_lower or "linear.x = 0" in code_lower or "publish_zero" in code_lower:
        score += SCORE_HAS_STOP_COMMAND
        breakdown.append(
            CandidateScoreBreakdown("has_stop_command", SCORE_HAS_STOP_COMMAND)
        )
    if "timeout" in code_lower or "monotonic" in code_lower or "deadline" in code_lower:
        score += SCORE_HAS_TIMEOUT
        breakdown.append(CandidateScoreBreakdown("has_timeout", SCORE_HAS_TIMEOUT))
    if "/cmd_vel_requested" in code:
        score += SCORE_USES_CMD_VEL_REQUESTED
        breakdown.append(
            CandidateScoreBreakdown(
                "uses_cmd_vel_requested", SCORE_USES_CMD_VEL_REQUESTED
            )
        )
    for fragment in FORBIDDEN_IMPORT_HINTS:
        if fragment in code:
            score += SCORE_FORBIDDEN_IMPORT
            breakdown.append(
                CandidateScoreBreakdown(
                    "forbidden_import",
                    SCORE_FORBIDDEN_IMPORT,
                    note=f"matched {fragment!r}",
                )
            )

    # Heuristic for bounded numeric inputs.
    if "bounded_speed" in code_lower or "speed=0." in code_lower:
        score += SCORE_BOUNDED_SPEED
        breakdown.append(CandidateScoreBreakdown("bounded_speed", SCORE_BOUNDED_SPEED))
    if "bounded_distance" in code_lower or "distance_m" in code_lower:
        score += SCORE_BOUNDED_DISTANCE
        breakdown.append(
            CandidateScoreBreakdown("bounded_distance", SCORE_BOUNDED_DISTANCE)
        )

    if candidate.explanation.strip():
        score += SCORE_EXPLANATION_PROVIDED
        breakdown.append(
            CandidateScoreBreakdown(
                "explanation_provided", SCORE_EXPLANATION_PROVIDED
            )
        )
    if candidate.known_uncertainties:
        score += SCORE_DISCLOSED_UNCERTAINTY
        breakdown.append(
            CandidateScoreBreakdown(
                "disclosed_uncertainty", SCORE_DISCLOSED_UNCERTAINTY
            )
        )

    # Penalise overconfident answers that the validator did not accept.
    if (
        candidate.confidence_label == CandidateConfidence.OVERCONFIDENT.value
        and not (validator.invoked and validator.accepted)
    ):
        score += SCORE_OVERCONFIDENT_WITHOUT_VALIDATION
        breakdown.append(
            CandidateScoreBreakdown(
                "overconfident_without_validation",
                SCORE_OVERCONFIDENT_WITHOUT_VALIDATION,
                note="model claimed high/overconfident but validator did not accept",
            )
        )

    return score, breakdown


def rank_candidates(
    triples: Iterable[
        tuple[SkillLLMCandidate, SkillLLMSanitizerResult, SkillLLMValidationResult]
    ],
) -> tuple[CandidateRanking, ...]:
    """Score every triple and return the ranking sorted high → low.

    Determinism: tied candidates are ordered by ``candidate_id`` so
    the ranking is fully reproducible.
    """

    scored: list[tuple[int, str, CandidateRanking]] = []
    for candidate, sanitizer, validator in triples:
        score, breakdown = _score_candidate(candidate, sanitizer, validator)
        accepted = sanitizer.accepted and validator.invoked and validator.accepted
        scored.append(
            (
                -score,  # negate so high score comes first
                candidate.candidate_id,
                CandidateRanking(
                    candidate_id=candidate.candidate_id,
                    rank=0,  # filled in below
                    score=score,
                    accepted=accepted,
                    safety_status=validator.safety_status,
                    breakdown=tuple(breakdown),
                ),
            )
        )
    scored.sort()
    ranked: list[CandidateRanking] = []
    for idx, (_, _, candidate_ranking) in enumerate(scored, start=1):
        from dataclasses import replace as _replace

        ranked.append(_replace(candidate_ranking, rank=idx))
    return tuple(ranked)


def ranking_to_dict(ranking: CandidateRanking) -> dict[str, object]:
    return {
        "candidate_id": ranking.candidate_id,
        "rank": ranking.rank,
        "score": ranking.score,
        "accepted": ranking.accepted,
        "safety_status": ranking.safety_status,
        "breakdown": [
            {"signal": b.signal, "delta": b.delta, "note": b.note}
            for b in ranking.breakdown
        ],
    }


__all__ = [
    "CandidateRanking",
    "CandidateScoreBreakdown",
    "FORBIDDEN_IMPORT_HINTS",
    "SCORE_BOUNDED_DISTANCE",
    "SCORE_BOUNDED_SPEED",
    "SCORE_DISCLOSED_UNCERTAINTY",
    "SCORE_EXPLANATION_PROVIDED",
    "SCORE_FORBIDDEN_IMPORT",
    "SCORE_HAS_STOP_COMMAND",
    "SCORE_HAS_TIMEOUT",
    "SCORE_OVERCONFIDENT_WITHOUT_VALIDATION",
    "SCORE_SANITIZER_REJECTED",
    "SCORE_USES_CMD_VEL_REQUESTED",
    "SCORE_VALIDATOR_ACCEPTED",
    "SCORE_VALIDATOR_REJECTED",
    "rank_candidates",
    "ranking_to_dict",
]
