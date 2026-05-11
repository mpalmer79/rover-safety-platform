"""Proposal audit artefacts.

The audit is a read-only record of one proposal pipeline run. It
contains the raw proposal, the sanitizer result, the compiler input
text, the compiler plan dict (or null if the sanitizer rejected),
the final outcome, and the verbatim safety-boundary disclaimer.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .adapter import AdapterResult
from .models import (
    MISSION_PROPOSAL_DISCLAIMER,
    PROPOSAL_LAYER_VERSION,
    ProposalAudit,
)


def build_audit(
    adapter_result: AdapterResult,
    *,
    generated_at_utc: str,
) -> ProposalAudit:
    return ProposalAudit(
        proposal=adapter_result.proposal,
        sanitizer_result=adapter_result.sanitizer_result,
        compiler_input=adapter_result.compiler_input,
        compiler_plan_json=adapter_result.compiler_plan,
        compiler_status=adapter_result.compiler_status,
        final_outcome=adapter_result.final_outcome,
        disclaimer=MISSION_PROPOSAL_DISCLAIMER,
        generated_at_utc=generated_at_utc,
    )


def _proposal_to_dict(audit: ProposalAudit) -> dict:
    proposal = audit.proposal
    return {
        "proposal_id": proposal.proposal_id,
        "source_text": proposal.source_text,
        "provider_name": proposal.provider_name,
        "provider_mode": proposal.provider_mode,
        "proposed_intent": proposal.proposed_intent,
        "proposed_location": proposal.proposed_location,
        "proposed_motion_style": proposal.proposed_motion_style,
        "proposed_constraints": list(proposal.proposed_constraints),
        "proposed_recovery_policy": proposal.proposed_recovery_policy,
        "confidence_label": proposal.confidence_label,
        "known_uncertainties": list(proposal.known_uncertainties),
        "raw_response": proposal.raw_response,
    }


def _sanitizer_to_dict(audit: ProposalAudit) -> dict:
    sr = audit.sanitizer_result
    return {
        "status": sr.status,
        "accepted": sr.accepted,
        "sanitized_intent": sr.sanitized_intent,
        "blocked_phrases": list(sr.blocked_phrases),
        "diagnostics": [asdict(d) for d in sr.diagnostics],
        "notes": list(sr.notes),
    }


def audit_to_dict(audit: ProposalAudit) -> dict:
    return {
        "proposal_layer_version": PROPOSAL_LAYER_VERSION,
        "proposal": _proposal_to_dict(audit),
        "sanitizer_result": _sanitizer_to_dict(audit),
        "compiler_input": audit.compiler_input,
        "compiler_status": audit.compiler_status,
        "compiler_plan": dict(audit.compiler_plan_json) if audit.compiler_plan_json else None,
        "final_outcome": audit.final_outcome,
        "disclaimer": audit.disclaimer,
        "generated_at_utc": audit.generated_at_utc,
    }


def render_audit_markdown(audit: ProposalAudit) -> str:
    proposal = audit.proposal
    sr = audit.sanitizer_result
    lines: list[str] = []
    lines.append(f"# Mission proposal audit: {proposal.proposal_id}")
    lines.append("")
    lines.append(f"_{audit.disclaimer}_")
    lines.append("")
    lines.append(f"- **Provider:** `{proposal.provider_name}` (mode `{proposal.provider_mode}`)")
    lines.append(f"- **Confidence:** `{proposal.confidence_label}`")
    lines.append(f"- **Sanitizer status:** `{sr.status}`")
    lines.append(f"- **Compiler status:** `{audit.compiler_status or 'not_invoked'}`")
    lines.append(f"- **Final outcome:** `{audit.final_outcome}`")
    lines.append(f"- **Generated:** {audit.generated_at_utc}")
    lines.append("")
    lines.append("## Source request")
    lines.append("")
    lines.append("```text")
    lines.append(proposal.source_text)
    lines.append("```")
    lines.append("")
    lines.append("## Provider proposal")
    lines.append("")
    lines.append(f"- intent: `{proposal.proposed_intent}`")
    lines.append(f"- location: `{proposal.proposed_location}`")
    lines.append(f"- motion style: `{proposal.proposed_motion_style}`")
    lines.append(
        "- constraints: "
        + (", ".join(f"`{c}`" for c in proposal.proposed_constraints) or "_(none)_")
    )
    lines.append(f"- recovery policy: `{proposal.proposed_recovery_policy}`")
    if proposal.known_uncertainties:
        lines.append("- known uncertainties:")
        for u in proposal.known_uncertainties:
            lines.append(f"  - {u}")
    lines.append("")
    lines.append("## Sanitizer")
    lines.append("")
    if sr.accepted:
        lines.append("Sanitizer accepted the proposal.")
        lines.append("")
        lines.append("Sanitized intent (compiler input):")
        lines.append("")
        lines.append("```text")
        lines.append(sr.sanitized_intent)
        lines.append("```")
    else:
        lines.append("Sanitizer **rejected** the proposal.")
        lines.append("")
        if sr.blocked_phrases:
            lines.append("Blocked phrases:")
            for phrase in sr.blocked_phrases:
                lines.append(f"- `{phrase}`")
        if sr.diagnostics:
            lines.append("")
            lines.append("Diagnostics:")
            for d in sr.diagnostics:
                lines.append(f"- `{d.code}` ({d.severity}): {d.message}")
    if sr.notes:
        lines.append("")
        lines.append("Sanitizer notes:")
        for n in sr.notes:
            lines.append(f"- {n}")
    lines.append("")
    lines.append("## Compiler outcome")
    lines.append("")
    if audit.compiler_plan_json is None:
        lines.append("The compiler was not invoked because the sanitizer rejected the proposal.")
    else:
        lines.append(f"Compiler returned status `{audit.compiler_status}`.")
        plan = audit.compiler_plan_json
        objectives = plan.get("objectives") or []  # type: ignore[union-attr]
        if isinstance(objectives, list) and objectives:
            lines.append("")
            lines.append("Compiled objectives:")
            for obj in objectives:
                if isinstance(obj, dict):
                    lines.append(f"- `{obj.get('label')}` ({obj.get('objective_kind')})")
    lines.append("")
    lines.append("## Authority statement")
    lines.append("")
    lines.append(
        "The deterministic mission compiler and the runtime safety "
        "supervisor remain authoritative. This proposal audit cannot "
        "authorise motion."
    )
    lines.append("")
    return "\n".join(lines)


def write_audit_bundle(audit: ProposalAudit, bundle_dir: Path) -> dict:
    """Write the per-proposal audit bundle.

    Layout:

        <bundle_dir>/proposal.json
        <bundle_dir>/sanitizer-result.json
        <bundle_dir>/compiler-input.json
        <bundle_dir>/compiler-result.json
        <bundle_dir>/proposal-audit.json
        <bundle_dir>/proposal-audit.md
    """

    bundle_dir = Path(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    proposal_path = bundle_dir / "proposal.json"
    sanitizer_path = bundle_dir / "sanitizer-result.json"
    compiler_input_path = bundle_dir / "compiler-input.json"
    compiler_result_path = bundle_dir / "compiler-result.json"
    audit_json_path = bundle_dir / "proposal-audit.json"
    audit_md_path = bundle_dir / "proposal-audit.md"

    audit_dict = audit_to_dict(audit)

    proposal_path.write_text(
        json.dumps(audit_dict["proposal"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sanitizer_path.write_text(
        json.dumps(audit_dict["sanitizer_result"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    compiler_input_path.write_text(
        json.dumps(
            {
                "proposal_id": audit.proposal.proposal_id,
                "compiler_input": audit.compiler_input,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    compiler_result_path.write_text(
        json.dumps(
            {
                "proposal_id": audit.proposal.proposal_id,
                "compiler_status": audit.compiler_status,
                "compiler_plan": audit_dict["compiler_plan"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    audit_json_path.write_text(
        json.dumps(audit_dict, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    audit_md_path.write_text(render_audit_markdown(audit), encoding="utf-8")

    return {
        "proposal": str(proposal_path),
        "sanitizer_result": str(sanitizer_path),
        "compiler_input": str(compiler_input_path),
        "compiler_result": str(compiler_result_path),
        "audit_json": str(audit_json_path),
        "audit_md": str(audit_md_path),
    }
