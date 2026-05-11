"""Deterministic intent parser.

The platform is **not safety-certified**. The parser takes a free
text mission intent, normalises it, splits it into clauses, and
matches each clause against the bounded template registry. It
never invents coordinates, objectives, or constraints.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from .models import (
    Diagnostic,
    ExtractedClause,
    SEVERITY_REJECTION,
    SEVERITY_WARNING,
)
from .templates import (
    AMBIGUITY_PHRASES,
    DANGEROUS_PHRASES,
    Template,
    all_templates,
    match_clause,
)


# Split on sentence-ending punctuation (".", ";") followed by
# whitespace, or on conjunctions. The whitespace-after-period rule
# avoids splitting numeric literals like "1.0" or "1.5 m/s".
_CLAUSE_SPLITTER = re.compile(
    r"\s*(?:\.\s+|;\s+|,\s+then\b|\s+then\b|\s+and\b|\s+also\b)\s*"
)


@dataclass(frozen=True)
class ParseResult:
    normalized_text: str
    clauses: tuple[ExtractedClause, ...]
    rejected_clauses: tuple[str, ...]
    diagnostics: tuple[Diagnostic, ...]


def _normalize(text: str) -> str:
    # Lower-case, collapse whitespace, strip trailing punctuation.
    out = text.lower().replace("\r", " ").replace("\n", " ")
    out = re.sub(r"[!?]+", ".", out)
    out = re.sub(r"\s+", " ", out).strip()
    if out.endswith("."):
        out = out[:-1]
    return out


def _split_clauses(text: str) -> tuple[str, ...]:
    pieces = [p.strip() for p in _CLAUSE_SPLITTER.split(text) if p.strip()]
    return tuple(pieces)


def _matches_ambiguity(clause: str) -> str | None:
    for phrase in AMBIGUITY_PHRASES:
        if phrase in clause:
            return phrase
    return None


def _matches_dangerous(clause: str) -> str | None:
    for phrase in DANGEROUS_PHRASES:
        if phrase in clause:
            return phrase
    return None


def parse_intent(text: str) -> ParseResult:
    """Parse a natural language mission intent deterministically.

    Returns the normalised text, a tuple of extracted clauses, a
    tuple of rejected (unmatched) clauses, and any diagnostics
    accumulated during parsing.
    """

    normalised = _normalize(text or "")
    clauses_raw = _split_clauses(normalised)

    accepted: list[ExtractedClause] = []
    rejected: list[str] = []
    diagnostics: list[Diagnostic] = []

    if not clauses_raw:
        diagnostics.append(
            Diagnostic(
                code="empty_intent",
                severity=SEVERITY_REJECTION,
                message="mission intent is empty after normalisation",
            )
        )
        return ParseResult(
            normalized_text=normalised,
            clauses=(),
            rejected_clauses=(),
            diagnostics=tuple(diagnostics),
        )

    for clause in clauses_raw:
        dangerous = _matches_dangerous(clause)
        if dangerous is not None:
            diagnostics.append(
                Diagnostic(
                    code="dangerous_unsupported_instruction",
                    severity=SEVERITY_REJECTION,
                    message=(
                        f"clause contains forbidden phrase: {dangerous!r}; the "
                        "compiler never accepts shell, code, or safety-bypass "
                        "constructs"
                    ),
                    clause=clause,
                )
            )
            rejected.append(clause)
            continue

        ambiguity = _matches_ambiguity(clause)

        match = match_clause(clause)
        if match is None:
            if ambiguity is not None:
                diagnostics.append(
                    Diagnostic(
                        code="ambiguous_clause",
                        severity=SEVERITY_WARNING,
                        message=(
                            "clause is ambiguous and was not converted to an "
                            f"objective: matched phrase {ambiguity!r}"
                        ),
                        clause=clause,
                    )
                )
            else:
                diagnostics.append(
                    Diagnostic(
                        code="unsupported_instruction",
                        severity=SEVERITY_WARNING,
                        message="clause did not match any supported template",
                        clause=clause,
                    )
                )
            rejected.append(clause)
            continue

        template, m = match
        slots = dict(template.extractor(m))
        # If a destination/zone/region slot contains an ambiguity
        # phrase keep the match but record an ambiguity diagnostic.
        for key, value in slots.items():
            if value and _matches_ambiguity(value) is not None:
                diagnostics.append(
                    Diagnostic(
                        code="ambiguous_destination",
                        severity=SEVERITY_WARNING,
                        message=(
                            "slot value is ambiguous; the compiler will "
                            "not invent a coordinate"
                        ),
                        clause=clause,
                        field=key,
                    )
                )
                rejected.append(clause)
                break
        else:
            accepted.append(
                ExtractedClause(
                    raw=clause,
                    normalized=clause,
                    template_id=template.template_id,
                    slots=slots,
                )
            )
            continue

    return ParseResult(
        normalized_text=normalised,
        clauses=tuple(accepted),
        rejected_clauses=tuple(rejected),
        diagnostics=tuple(diagnostics),
    )


__all__ = [
    "ParseResult",
    "parse_intent",
]
