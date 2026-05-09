"""Per-run evidence directory layout under ``evidence/runtime/<run_id>/``.

The layout is documented in
``docs/RUNTIME_VALIDATION_RUNBOOK.md``. This module provides a small
helper class so probes write to consistent paths and the orchestrator
can summarise them honestly.

The list of expected files is the canonical contract. A probe that
cannot run produces its file with a ``not_executed`` payload rather
than skipping the file silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


RUNTIME_EVIDENCE_FILES: tuple[str, ...] = (
    "runtime-validation.json",
    "runtime-validation.md",
    "topic-snapshot.json",
    "node-snapshot.json",
    "tf-tree.txt",
    "tf-snapshot.json",
    "command-path-audit.json",
    "launch-log.txt",
    "known-limitations.md",
)


@dataclass(frozen=True)
class EvidenceLayout:
    root: Path
    run_id: str

    @property
    def run_dir(self) -> Path:
        return self.root / self.run_id

    def ensure(self) -> "EvidenceLayout":
        self.run_dir.mkdir(parents=True, exist_ok=True)
        return self

    def path(self, name: str) -> Path:
        if name not in RUNTIME_EVIDENCE_FILES:
            raise ValueError(
                f"unknown runtime evidence file: {name!r}. "
                f"Add it to RUNTIME_EVIDENCE_FILES first."
            )
        return self.run_dir / name


def new_runtime_run_id(prefix: str = "runtime") -> str:
    """Return a deterministic run id for static-only or live runs.

    The format is ``<prefix>-YYYYMMDDTHHMMSSZ`` so multiple runs can
    coexist on a developer workstation. Tests that need a stable id
    pass an explicit value rather than relying on this helper.
    """

    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{stamp}"
