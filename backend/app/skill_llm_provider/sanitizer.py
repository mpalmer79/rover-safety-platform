"""Sanitizer for raw LLM candidate output.

The sanitizer is a **tripwire and deterrence layer** between an
untrusted provider and the deterministic Phase 15A skill validator. It
is not a sandboxed execution boundary; generated code is reviewed by a
human and copied to their clipboard, never executed by this service.
Hostile code can always defeat a pure-textual filter (string-builder
imports, unicode obfuscation, exec-of-string, etc.) — the value of
this layer is that it catches the common shapes, surfaces them to the
reviewer, and refuses to advance them automatically.

The Python AST scan (:func:`_check_python_ast`) is a structural
secondary check for code-shaped fields. The legacy textual filter
remains for non-Python providers and free-text fields.

Allowed:
* ``/cmd_vel_requested`` in code or interfaces
* mentions of ``/cmd_vel`` in plain English inside the explanation
  (so a model can correctly describe why direct actuator publication
  is forbidden) — but **not** inside ``code`` or ``declared_topics``.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Iterable

from .models import (
    CandidateRejectionReason,
    SkillLLMCandidate,
    SkillLLMSanitizerResult,
)


# ---------------------------------------------------------------------
# _LEGACY_TEXTUAL_FILTER - regex-based scan retained for non-Python
# providers and natural-language fields. Treat as deterrence: anything
# that looks like a known-bad fragment is surfaced; obfuscation can
# evade this layer and that is expected. The AST scan below is the
# structural check for Python code.
# ---------------------------------------------------------------------
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


_FORBIDDEN_PY_MODULES: frozenset[str] = frozenset(
    {
        "subprocess",
        "socket",
        "urllib",
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "cohere",
        "ctypes",
        "marshal",
        "pickle",
        "pty",
    }
)
# ``os`` is allowed only when every access is gated to os.path.*.
_OS_PATH_ALLOWED_PREFIX: str = "path"


@dataclass(frozen=True)
class _Match:
    text: str
    code: str
    message: str
    span: tuple[int, int]


def _scan(text: str) -> list[_Match]:
    """Return matches for the legacy regex filter.

    The span is preserved so sentence-scoped exemptions can be applied
    without re-running the whole scan.
    """

    if not text:
        return []
    out: list[_Match] = []
    for pattern, code, message in FORBIDDEN_FRAGMENTS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match is not None:
            out.append(_Match(match.group(0), code, message, match.span()))
    return out


_SENTENCE_BOUNDARY = re.compile(r"[.!?\n]")


def _sentence_containing(text: str, span: tuple[int, int]) -> str:
    """Return the sentence around ``span`` in ``text``.

    Sentence boundaries are ``.``, ``!``, ``?``, and newline. The
    returned slice excludes the boundary characters themselves.
    Used to scope descriptive-use exemptions: a "do not ..." phrase
    later in the field does not exempt an unrelated imperative
    earlier in the field.
    """

    start, end = span
    left = 0
    for m in _SENTENCE_BOUNDARY.finditer(text, 0, start):
        left = m.end()
    right_match = _SENTENCE_BOUNDARY.search(text, end)
    right = right_match.start() if right_match is not None else len(text)
    return text[left:right]


def _strip_python_comments(code: str) -> str:
    """Remove the ``# ...`` portion of each line of code."""

    out: list[str] = []
    for line in code.splitlines():
        out.append(line.split("#", 1)[0])
    return "\n".join(out)


def _references_direct_cmd_vel(text: str) -> bool:
    """Return True if executable text references ``/cmd_vel`` directly."""

    stripped = _strip_python_comments(text)
    for approved in ("/cmd_vel_requested", "/cmd_vel_authorized"):
        stripped = stripped.replace(approved, "")
    return re.search(r"/cmd_vel(?![_a-zA-Z0-9])", stripped) is not None


@dataclass(frozen=True)
class _AstDiagnostic:
    code: str
    message: str
    fragment: str


def _import_module_root(name: str) -> str:
    return (name or "").split(".", 1)[0]


def _check_python_ast(code: str) -> list[_AstDiagnostic]:
    """Structural AST-based check for Python code.

    Looks for: forbidden module imports, calls to eval/exec/compile/
    __import__/getattr-with-dunder, attribute access on __builtins__,
    and unbounded ``while``/``for`` loops without ``break``.

    A syntax error becomes a structured rejection, not a crash.
    """

    out: list[_AstDiagnostic] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        out.append(
            _AstDiagnostic(
                code=CandidateRejectionReason.INVALID_PROVIDER_OUTPUT.value,
                message=f"python AST parse failed: {exc.msg} at line {exc.lineno}",
                fragment="<syntax error>",
            )
        )
        return out

    # Walk imports.
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = _import_module_root(alias.name)
                if root in _FORBIDDEN_PY_MODULES:
                    out.append(
                        _AstDiagnostic(
                            code=CandidateRejectionReason.NETWORK_ACCESS.value
                            if root in {"socket", "urllib", "requests", "httpx", "openai", "anthropic", "cohere"}
                            else CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value,
                            message=f"forbidden import: {alias.name}",
                            fragment=f"import {alias.name}",
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            root = _import_module_root(node.module or "")
            if root in _FORBIDDEN_PY_MODULES:
                out.append(
                    _AstDiagnostic(
                        code=CandidateRejectionReason.NETWORK_ACCESS.value
                        if root in {"socket", "urllib", "requests", "httpx", "openai", "anthropic", "cohere"}
                        else CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value,
                        message=f"forbidden from-import: {node.module}",
                        fragment=f"from {node.module} import ...",
                    )
                )
        elif isinstance(node, ast.Attribute):
            # Block attribute access on __builtins__/globals/vars when
            # used to reach hidden surface.
            target = node.value
            if isinstance(target, ast.Name) and target.id in {"__builtins__", "globals", "vars"}:
                out.append(
                    _AstDiagnostic(
                        code=CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value,
                        message=f"attribute access on {target.id} is forbidden",
                        fragment=f"{target.id}.{node.attr}",
                    )
                )
        elif isinstance(node, ast.Call):
            func = node.func
            name: str | None = None
            if isinstance(func, ast.Name):
                name = func.id
            if name in {"eval", "exec", "compile", "__import__"}:
                out.append(
                    _AstDiagnostic(
                        code=CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value,
                        message=f"call to {name}() is forbidden",
                        fragment=f"{name}(...)",
                    )
                )
            elif name == "getattr" and node.args:
                # getattr(x, "__dunder__") is the classic introspection
                # bypass.
                first = node.args[1] if len(node.args) >= 2 else None
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    if first.value.startswith("__") and first.value.endswith("__"):
                        out.append(
                            _AstDiagnostic(
                                code=CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value,
                                message=f"getattr with dunder name {first.value!r}",
                                fragment=f"getattr(..., {first.value!r})",
                            )
                        )

    # Walk loops looking for unbounded constructs.
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            test = node.test
            truthy_constant = (
                isinstance(test, ast.Constant) and bool(test.value)
            ) or (isinstance(test, ast.Name) and test.id == "True")
            has_break = any(isinstance(c, ast.Break) for c in ast.walk(node))
            if truthy_constant and not has_break:
                out.append(
                    _AstDiagnostic(
                        code=CandidateRejectionReason.UNBOUNDED_MOTION.value,
                        message="while-true loop with no break",
                        fragment="while <truthy>: ...",
                    )
                )
        elif isinstance(node, ast.For):
            # ``for _ in itertools.count():`` or any explicit infinite
            # iterator is treated as unbounded.
            it = node.iter
            if isinstance(it, ast.Call):
                func = it.func
                full = ""
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    full = f"{func.value.id}.{func.attr}"
                elif isinstance(func, ast.Name):
                    full = func.id
                if full in {"itertools.count", "itertools.cycle", "iter"}:
                    has_break = any(isinstance(c, ast.Break) for c in ast.walk(node))
                    if not has_break:
                        out.append(
                            _AstDiagnostic(
                                code=CandidateRejectionReason.UNBOUNDED_MOTION.value,
                                message=f"unbounded for-loop iterator: {full}",
                                fragment=f"for ... in {full}(...)",
                            )
                        )

    # Special-case ``os`` imports: only allow when every Attribute
    # access of the form ``os.<attr>`` uses attr == "path" (or a child).
    has_os_import = False
    os_attr_violations: list[_AstDiagnostic] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os" or alias.name.startswith("os."):
                    has_os_import = True
        elif isinstance(node, ast.ImportFrom) and (node.module or "") == "os":
            has_os_import = True
        elif isinstance(node, ast.Attribute):
            target = node.value
            if isinstance(target, ast.Name) and target.id == "os":
                if node.attr != _OS_PATH_ALLOWED_PREFIX:
                    os_attr_violations.append(
                        _AstDiagnostic(
                            code=CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value,
                            message=f"os.{node.attr} not in allowed subset (only os.path.*)",
                            fragment=f"os.{node.attr}",
                        )
                    )
    if has_os_import and os_attr_violations:
        out.extend(os_attr_violations)

    return out


def sanitize_candidate(candidate: SkillLLMCandidate) -> SkillLLMSanitizerResult:
    """Run every sanitizer rule against the candidate."""

    reason_codes: list[str] = []
    blocked: list[str] = []
    notes: list[str] = []

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
        for m in _scan(text):
            reason_codes.append(m.code)
            blocked.append(f"{field_name}:{m.text}")
            notes.append(f"{field_name}: {m.message}")

    # Sentence-scoped explanation allowlist. A "do not / must not /
    # never" exemption only applies to the SENTENCE containing the
    # matched fragment, not the whole field. Otherwise an attacker
    # places a benign disclaimer at the top and an imperative
    # immediately below, slipping past.
    for field_name, text in explanation_scan:
        for m in _scan(text):
            if m.code in {
                CandidateRejectionReason.SAFETY_OVERRIDE.value,
                CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value,
            }:
                sentence = _sentence_containing(text, m.span).lower()
                if "do not" in sentence or "must not" in sentence or "never" in sentence:
                    notes.append(
                        f"{field_name}: descriptive use of '{m.text}' allowed (sentence-scoped)"
                    )
                    continue
            reason_codes.append(m.code)
            blocked.append(f"{field_name}:{m.text}")
            notes.append(f"{field_name}: {m.message}")

    # AST-based structural check for the candidate's code field.
    for diag in _check_python_ast(candidate.code):
        reason_codes.append(diag.code)
        blocked.append(f"code:{diag.fragment}")
        notes.append(f"code (ast): {diag.message}")

    # Direct /cmd_vel check (executable text only - strips comments +
    # approved topic suffixes).
    if _references_direct_cmd_vel(candidate.code):
        reason_codes.append(CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value)
        blocked.append("code:/cmd_vel")
        notes.append("code: direct /cmd_vel publication is forbidden")
    for topic in candidate.declared_topics:
        if topic.strip() == "/cmd_vel":
            reason_codes.append(CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value)
            blocked.append("declared_topics:/cmd_vel")
            notes.append("declared_topics: /cmd_vel is forbidden; use /cmd_vel_requested")

    if candidate.confidence_label == "overconfident":
        notes.append("provider declares confidence='overconfident'; treat as suspect")

    if reason_codes:
        return SkillLLMSanitizerResult(
            status="rejected",
            accepted=False,
            reason_codes=tuple(dict.fromkeys(reason_codes)),
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
