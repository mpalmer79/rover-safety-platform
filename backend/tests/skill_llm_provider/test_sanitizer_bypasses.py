"""Bypass coverage for the sanitizer's AST and sentence-scoped checks.

These tests fail on the pre-#5/#6 implementation: the legacy regex
filter passed string-builder imports, dunder-getattr eval, ``eval (x)``
with a space, ``while 1`` (vs ``while True``), and ``for _ in
itertools.count():``. The sentence-scoped exemption test exposes the
pre-fix behaviour where a benign "do not" disclaimer anywhere in the
explanation could shield an imperative elsewhere.
"""

from __future__ import annotations

import pytest

from app.skill_llm_provider.models import (
    CandidateRejectionReason,
    SkillLLMCandidate,
)
from app.skill_llm_provider.sanitizer import (
    _sentence_containing,
    sanitize_candidate,
)


def _candidate(*, code: str = "", explanation: str = "") -> SkillLLMCandidate:
    return SkillLLMCandidate(
        candidate_id="c-test",
        source_text="",
        provider_mode="fixture",
        provider_name="fixture",
        model_name="test",
        language="python_ros2",
        skill_type="",
        code=code,
        explanation=explanation,
        declared_topics=(),
        declared_interfaces=(),
        declared_safety_constraints=(),
        confidence_label="low",
        known_uncertainties=(),
        raw_provider_payload="",
    )


# --- Sentence-scope (#5) -------------------------------------------------

def test_sentence_scope_exempts_only_the_matching_sentence() -> None:
    """The exempting "never" applies only to its own sentence.

    Before the fix this would slip past — "never" anywhere in the
    explanation exempted every match.
    """

    explanation = (
        "You should never touch the rover. "
        "Now disable the safety supervisor."
    )
    result = sanitize_candidate(_candidate(explanation=explanation))
    assert not result.accepted
    assert CandidateRejectionReason.SAFETY_OVERRIDE.value in result.reason_codes


def test_sentence_scope_keeps_legit_descriptive_use() -> None:
    """A "do not / never" co-located with the match is still exempt."""

    explanation = "Operators must never disable the safety supervisor."
    result = sanitize_candidate(_candidate(explanation=explanation))
    assert result.accepted, result.reason_codes


def test_sentence_containing_handles_newlines_and_endings() -> None:
    text = "Sentence one. Match here please.\nNext sentence."
    span = (text.index("Match"), text.index("Match") + len("Match"))
    assert _sentence_containing(text, span).strip() == "Match here please"


# --- AST-based code checks (#6) -----------------------------------------

REJECT_SAMPLES = [
    pytest.param("eval (x)\n", id="eval-with-space"),
    pytest.param("__import__('sub' + 'process')\n", id="dynamic-import-call"),
    pytest.param("from anthropic import Anthropic\n", id="from-anthropic"),
    pytest.param("import anthropic as a\n", id="import-anthropic-alias"),
    pytest.param("getattr(__builtins__, '__import__')('os')\n", id="getattr-dunder"),
    pytest.param("while 1:\n    pass\n", id="while-1-no-break"),
    pytest.param(
        "import itertools\nfor _ in itertools.count():\n    pass\n",
        id="itertools-count-no-break",
    ),
]


@pytest.mark.parametrize("code", REJECT_SAMPLES)
def test_ast_rejects_known_bypasses(code: str) -> None:
    result = sanitize_candidate(_candidate(code=code))
    assert not result.accepted, f"expected rejection for: {code!r}"


ACCEPT_SAMPLES = [
    pytest.param("import os\nos.path.join('a', 'b')\n", id="os-path-only"),
    pytest.param("# eval (foo) is forbidden\nx = 1\n", id="eval-in-comment"),
]


@pytest.mark.parametrize("code", ACCEPT_SAMPLES)
def test_ast_accepts_benign_code(code: str) -> None:
    result = sanitize_candidate(_candidate(code=code))
    # We don't assert the inverse (no rejection-of-any-kind) because
    # other validators may still flag missing tokens; we only check
    # that the AST layer didn't reject this specific shape.
    assert (
        CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value not in result.reason_codes
    ), result.notes
    assert (
        CandidateRejectionReason.UNBOUNDED_MOTION.value not in result.reason_codes
    ), result.notes


def test_ast_syntax_error_becomes_structured_rejection() -> None:
    """A SyntaxError must not crash the sanitizer — it must reject structurally."""

    result = sanitize_candidate(_candidate(code="def(:\n"))
    assert not result.accepted
    assert (
        CandidateRejectionReason.INVALID_PROVIDER_OUTPUT.value in result.reason_codes
    )
