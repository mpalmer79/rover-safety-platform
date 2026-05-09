"""Run manifest helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain.replay import RunMetadata


@dataclass(frozen=True, slots=True)
class RunManifest:
    """A read-only view of one run directory."""

    run_dir: Path
    metadata: RunMetadata

    @property
    def events_path(self) -> Path:
        return self.run_dir / "events.jsonl"

    @property
    def states_path(self) -> Path:
        return self.run_dir / "states.jsonl"

    @property
    def commands_path(self) -> Path:
        return self.run_dir / "commands.jsonl"

    @property
    def sensors_path(self) -> Path:
        return self.run_dir / "sensor_readings.jsonl"

    @property
    def summary_path(self) -> Path:
        return self.run_dir / "incident-summary.md"

    def has_required_artifacts(self) -> bool:
        return all(
            p.exists()
            for p in (
                self.run_dir / "metadata.json",
                self.events_path,
                self.states_path,
                self.commands_path,
                self.sensors_path,
                self.summary_path,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_dir": str(self.run_dir),
            "metadata": self.metadata.to_dict(),
            "has_required_artifacts": self.has_required_artifacts(),
        }


def write_manifest(run_dir: Path, metadata: RunMetadata) -> Path:
    path = run_dir / "metadata.json"
    path.write_text(json.dumps(metadata.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path
