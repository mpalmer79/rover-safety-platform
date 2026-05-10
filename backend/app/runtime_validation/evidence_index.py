"""Evidence index: enumerate retained qualification runs.

Phase 5 retains every qualification run under
``evidence/runtime/<run_id>/``. The evidence index is a manifest of
those runs so reviewers can navigate without ad-hoc filesystem
queries:

* one row per run, ordered chronologically (newest first);
* each row carries the run id, mode, status, generated_at_utc,
  scenarios exercised, and a relative path to the per-run
  ``runtime-validation.json`` and ``qualification-summary.md``.

The index is materialised as JSON (``evidence/runtime/index.json``)
and Markdown (``docs/EVIDENCE_INDEX.md``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class EvidenceIndexRow:
    run_id: str
    mode: str
    status: str
    generated_at_utc: str
    runtime_validation_path: str
    qualification_summary_path: str
    host_qualification_path: str
    scenarios: tuple[str, ...] = ()
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "status": self.status,
            "generated_at_utc": self.generated_at_utc,
            "runtime_validation_path": self.runtime_validation_path,
            "qualification_summary_path": self.qualification_summary_path,
            "host_qualification_path": self.host_qualification_path,
            "scenarios": list(self.scenarios),
            "notes": self.notes,
        }


@dataclass
class EvidenceIndex:
    root: Path
    rows: list[EvidenceIndexRow] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "root": str(self.root),
            "rows": [r.as_dict() for r in self.rows],
        }


def build_evidence_index(*, evidence_root: Path) -> EvidenceIndex:
    """Build the index by scanning every immediate subdirectory of ``evidence_root``.

    Files ``runtime-validation.json``, ``qualification-summary.md``,
    and ``host-qualification.json`` (when present) are treated as the
    canonical per-run manifest. Runs that lack ``runtime-validation.json``
    are still listed (with whatever metadata is available); they are
    not silently dropped.
    """

    index = EvidenceIndex(root=evidence_root)
    if not evidence_root.exists():
        return index
    # We sort by ``generated_at_utc`` descending where available so the
    # newest run appears first. Directories that lack a parsable
    # ``runtime-validation.json`` fall back to a reverse alpha sort by
    # run id; they sort to the bottom because we use empty string as
    # the timestamp and tie-break with the run id.
    candidates_with_meta: list[tuple[str, str, Path]] = []
    for p in evidence_root.iterdir():
        if not p.is_dir():
            continue
        rv = p / "runtime-validation.json"
        ts = ""
        if rv.exists():
            try:
                payload = json.loads(rv.read_text(encoding="utf-8"))
                ts = payload.get("generated_at_utc", "") or ""
            except json.JSONDecodeError:
                pass
        candidates_with_meta.append((ts, p.name, p))
    candidates_with_meta.sort(key=lambda row: (row[0], row[1]), reverse=True)
    for _ts, _name, run_dir in candidates_with_meta:
        runtime_validation = run_dir / "runtime-validation.json"
        host_qualification = run_dir / "host-qualification.json"
        qualification_summary = run_dir / "qualification-summary.md"
        run_id = run_dir.name
        mode = "unknown"
        status = "unknown"
        generated_at_utc = ""
        scenarios: list[str] = []
        notes = ""
        if runtime_validation.exists():
            try:
                payload = json.loads(runtime_validation.read_text(encoding="utf-8"))
                mode = payload.get("mode", "unknown")
                status = payload.get("status", "unknown")
                generated_at_utc = payload.get("generated_at_utc", "")
                run_id = payload.get("run_id", run_id)
            except json.JSONDecodeError:
                notes = "runtime-validation.json failed to parse"
        else:
            notes = "no runtime-validation.json (run was not orchestrated)"
        # Scenarios are listed in any per-scenario summary file
        # (runtime-capture-*.json or qualification-scenario-*.json).
        for path in run_dir.glob("runtime-capture-*.json"):
            scenarios.append(path.stem.replace("runtime-capture-", ""))
        for path in run_dir.glob("qualification-scenario-*.json"):
            scenarios.append(path.stem.replace("qualification-scenario-", ""))
        index.rows.append(
            EvidenceIndexRow(
                run_id=run_id,
                mode=mode,
                status=status,
                generated_at_utc=generated_at_utc,
                runtime_validation_path=(
                    str(runtime_validation.relative_to(evidence_root))
                    if runtime_validation.exists()
                    else ""
                ),
                qualification_summary_path=(
                    str(qualification_summary.relative_to(evidence_root))
                    if qualification_summary.exists()
                    else ""
                ),
                host_qualification_path=(
                    str(host_qualification.relative_to(evidence_root))
                    if host_qualification.exists()
                    else ""
                ),
                scenarios=tuple(sorted(set(scenarios))),
                notes=notes,
            )
        )
    return index


def write_evidence_index(
    index: EvidenceIndex,
    *,
    json_path: Optional[Path] = None,
    markdown_path: Optional[Path] = None,
) -> None:
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(index.as_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_evidence_index_md(index), encoding="utf-8")


def render_evidence_index_md(index: EvidenceIndex) -> str:
    lines: list[str] = []
    lines.append("# Evidence Index")
    lines.append("")
    lines.append(
        "_Generated by `rover_ws/tools/qualified_runtime_run.py` (or "
        "directly via `tools/generate_evidence_index.py`). Each row "
        "lists a retained qualification run under "
        "`evidence/runtime/<run_id>/`. The platform is **not "
        "safety-certified**; this index demonstrates evidence "
        "discipline._"
    )
    lines.append("")
    lines.append(f"- **Evidence root:** `{index.root}`")
    lines.append(f"- **Runs retained:** {len(index.rows)}")
    lines.append("")
    if not index.rows:
        lines.append("_No qualification runs retained yet._")
        lines.append("")
        return "\n".join(lines)
    lines.append("## Runs")
    lines.append("")
    lines.append(
        "| Run id | Generated (UTC) | Mode | Status | Scenarios | Runtime validation |"
    )
    lines.append("|---|---|---|---|---|---|")
    for row in index.rows:
        scenarios = ", ".join(f"`{s}`" for s in row.scenarios) or "-"
        rv = f"`{row.runtime_validation_path}`" if row.runtime_validation_path else "-"
        lines.append(
            f"| `{row.run_id}` | {row.generated_at_utc} | `{row.mode}` | "
            f"`{row.status}` | {scenarios} | {rv} |"
        )
        if row.notes:
            lines.append(f"|   | _{row.notes}_ |   |   |   |   |")
    lines.append("")
    return "\n".join(lines)
