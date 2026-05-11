#!/usr/bin/env python3
"""Generate the canonical mission-library bundle from EXAMPLES.

Run from the repo root:

    python rover_ws/tools/_generate_mission_library.py

The platform is **not safety-certified**.
"""

from __future__ import annotations

import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.natural_language_mission import (  # noqa: E402
    COMPILE_STATUS_REJECTED,
    EXAMPLES,
    build_audit,
    compile_intent,
    write_audit,
    write_plan,
    write_replay_binding,
)


GENERATED_AT_UTC = "2026-05-12T00:00:00+00:00"


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    intents = repo / "mission-library" / "intents"
    compiled = repo / "mission-library" / "compiled"
    rejected = repo / "mission-library" / "rejected"
    audits = repo / "mission-library" / "audits"
    examples_dir = repo / "mission-library" / "examples"
    for d in (intents, compiled, rejected, audits, examples_dir):
        d.mkdir(parents=True, exist_ok=True)

    for ex in EXAMPLES:
        intent_path = intents / f"{ex.example_id}.txt"
        intent_path.write_text(ex.intent + "\n", encoding="utf-8")

        plan = compile_intent(
            ex.intent,
            plan_id=ex.example_id,
            generated_at_utc=GENERATED_AT_UTC,
            odd_profile_id=ex.odd_profile_id,
        )
        target_root = rejected if plan.status == COMPILE_STATUS_REJECTED else compiled
        json_path = target_root / f"{ex.example_id}.json"
        md_path = target_root / f"{ex.example_id}.md"
        binding_path = target_root / f"{ex.example_id}-replay-binding.json"
        write_plan(plan, json_path=json_path, md_path=md_path)
        write_replay_binding(plan, binding_path)

        audit_json = audits / f"{ex.example_id}-audit.json"
        audit_md = audits / f"{ex.example_id}-audit.md"
        write_audit(plan, json_path=audit_json, md_path=audit_md)

        # Example summary card (concise).
        summary = examples_dir / f"{ex.example_id}.md"
        summary.write_text(
            "\n".join(
                [
                    f"# Example: {ex.example_id}",
                    "",
                    f"_{ex.notes}_",
                    "",
                    f"- Expected status: `{ex.expected_status}`",
                    f"- Actual status: `{plan.status}`",
                    f"- Risk: `{plan.risk.band}` (score `{plan.risk.score}`)",
                    f"- Objectives: {len(plan.objectives)}",
                    f"- Constraints: {len(plan.constraints)}",
                    f"- Diagnostics: {len(plan.diagnostics)}",
                    "",
                    "## Intent",
                    "",
                    f"> {ex.intent}",
                    "",
                    "## Files",
                    "",
                    f"- plan json: `mission-library/{target_root.name}/{ex.example_id}.json`",
                    f"- plan md:   `mission-library/{target_root.name}/{ex.example_id}.md`",
                    f"- audit:     `mission-library/audits/{ex.example_id}-audit.json`",
                    f"- replay:    `mission-library/{target_root.name}/{ex.example_id}-replay-binding.json`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
