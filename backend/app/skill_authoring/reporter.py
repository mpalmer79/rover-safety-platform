"""Filesystem reporter for skill audit bundles.

Layout:

    Accepted skill:
        <bundle_dir>/request.json
        <bundle_dir>/generated-skill.json
        <bundle_dir>/code.py            (or code.md / code.cpp)
        <bundle_dir>/safety-review.json
        <bundle_dir>/diagnostics.json
        <bundle_dir>/code-card.json
        <bundle_dir>/skill-report.md

    Rejected / unsupported / ambiguous / validation_failed:
        <bundle_dir>/request.json
        <bundle_dir>/diagnostics.json
        <bundle_dir>/rejection-report.md
"""

from __future__ import annotations

import json
from pathlib import Path

from .audit import (
    audit_to_dict,
    build_audit_bundle,
    candidate_to_dict,
    generated_skill_to_dict,
    render_rejection_markdown,
    render_skill_report_markdown,
    request_to_dict,
)
from .models import (
    SkillAuditBundle,
    SkillGenerationResult,
    SkillGenerationStatus,
    SkillLanguage,
)


def _ext_for(language: str) -> str:
    if language == SkillLanguage.PYTHON_ROS2.value:
        return "py"
    if language == SkillLanguage.CPP_ROS2.value:
        return "cpp"
    return "md"


def _dump_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_audit_files(
    result: SkillGenerationResult,
    bundle_dir: Path,
) -> tuple[SkillAuditBundle, dict]:
    """Write the bundle and return ``(audit, paths_written)``."""

    bundle_dir = Path(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    audit = build_audit_bundle(result)
    paths: dict[str, str] = {}

    request_path = bundle_dir / "request.json"
    diag_path = bundle_dir / "diagnostics.json"
    _dump_json(request_path, request_to_dict(audit.request))
    paths["request"] = str(request_path)
    _dump_json(
        diag_path,
        {
            "status": audit.status,
            "rejection_reason": audit.rejection_reason,
            "diagnostics": [
                {
                    "code": d.code,
                    "severity": d.severity,
                    "message": d.message,
                    "parameter": d.parameter,
                }
                for d in audit.diagnostics
            ],
            "disclaimer": audit.disclaimer,
        },
    )
    paths["diagnostics"] = str(diag_path)

    if audit.status == SkillGenerationStatus.GENERATED.value:
        skill = audit.generated_skill
        assert skill is not None
        skill_path = bundle_dir / "generated-skill.json"
        review_path = bundle_dir / "safety-review.json"
        card_path = bundle_dir / "code-card.json"
        code_path = bundle_dir / f"code.{_ext_for(skill.language)}"
        report_path = bundle_dir / "skill-report.md"

        skill_dict = generated_skill_to_dict(skill)
        _dump_json(skill_path, skill_dict)
        _dump_json(review_path, skill_dict["safety_review"])
        _dump_json(card_path, skill_dict["code_card"])
        code_path.write_text(skill.code, encoding="utf-8")
        report_path.write_text(render_skill_report_markdown(audit), encoding="utf-8")

        paths["generated_skill"] = str(skill_path)
        paths["safety_review"] = str(review_path)
        paths["code_card"] = str(card_path)
        paths["code"] = str(code_path)
        paths["skill_report"] = str(report_path)
    else:
        report_path = bundle_dir / "rejection-report.md"
        report_path.write_text(render_rejection_markdown(audit), encoding="utf-8")
        paths["rejection_report"] = str(report_path)
        # Always write candidate.json so reviewers can see what the
        # parser saw before rejection.
        cand_path = bundle_dir / "candidate.json"
        _dump_json(cand_path, candidate_to_dict(audit.candidate))
        paths["candidate"] = str(cand_path)

    return audit, paths
