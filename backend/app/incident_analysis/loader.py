"""Evidence loader for the incident analysis layer.

Reads the artefacts produced by Phase-3, Phase-4, and Phase-5 in a
defensive way: missing files, malformed JSON, schema drift, empty
event streams, and inconsistent run / scenario ids all become
:class:`LoaderWarning` entries on the returned bundle. The loader
never silently swallows errors and never invents synthetic events.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from app.incident_analysis.models import (
    EvidenceOrigin,
    IncidentEvidenceManifest,
    LoaderWarning,
)


_RUNTIME_EVIDENCE_FILES: tuple[str, ...] = (
    "runtime-validation.json",
    "runtime-validation.md",
    "topic-snapshot.json",
    "node-snapshot.json",
    "tf-snapshot.json",
    "tf-tree.txt",
    "command-path-audit.json",
    "host-qualification.json",
    "qualification-summary.json",
    "qualification-summary.md",
    "live-runtime-status.md",
    "regression-report.json",
    "known-limitations.md",
)


_SCENARIO_EVIDENCE_FILES: tuple[str, ...] = (
    "evidence.json",
    "evidence.md",
    "events-summary.md",
    "replay-integrity.json",
    "command-audit.json",
    "safety-transition-audit.json",
)


@dataclass
class LoadedRuntimeEvidence:
    """The contents of an ``evidence/runtime/<run_id>/`` directory."""

    run_dir: Path
    run_id: Optional[str]
    runtime_validation: Optional[dict] = None
    topic_snapshot: Optional[dict] = None
    node_snapshot: Optional[dict] = None
    tf_snapshot: Optional[dict] = None
    command_path_audit: Optional[dict] = None
    host_qualification: Optional[dict] = None
    qualification_summary: Optional[dict] = None
    regression_report: Optional[dict] = None
    raw_files: dict[str, str] = field(default_factory=dict)
    """Raw text contents of Markdown / text files keyed by filename."""

    warnings: list[LoaderWarning] = field(default_factory=list)

    def files_present(self) -> tuple[str, ...]:
        """Names (relative to ``run_dir``) that loaded successfully."""

        present: list[str] = []
        for name, payload in (
            ("runtime-validation.json", self.runtime_validation),
            ("topic-snapshot.json", self.topic_snapshot),
            ("node-snapshot.json", self.node_snapshot),
            ("tf-snapshot.json", self.tf_snapshot),
            ("command-path-audit.json", self.command_path_audit),
            ("host-qualification.json", self.host_qualification),
            ("qualification-summary.json", self.qualification_summary),
            ("regression-report.json", self.regression_report),
        ):
            if payload is not None:
                present.append(name)
        present.extend(self.raw_files.keys())
        return tuple(sorted(set(present)))

    def is_static_only(self) -> bool:
        """Heuristic: aggregate runtime status indicates static-only mode."""

        if self.runtime_validation is None:
            return False
        return self.runtime_validation.get("mode") == "static-only"


@dataclass
class LoadedScenarioEvidence:
    """The contents of an ``evidence/scenarios/<scenario_id>/`` dir."""

    scenario_dir: Path
    scenario_id: Optional[str]
    evidence: Optional[dict] = None
    replay_integrity: Optional[dict] = None
    command_audit: Optional[dict] = None
    safety_transition_audit: Optional[dict] = None
    raw_files: dict[str, str] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    """Parsed events.jsonl entries from the run dir referenced by
    the scenario evidence (if present)."""

    run_dir: Optional[Path] = None
    """Path to the underlying ``runs/<run_id>/`` dir referenced by
    the scenario evidence; ``None`` when the runs dir cannot be
    located."""

    warnings: list[LoaderWarning] = field(default_factory=list)

    def files_present(self) -> tuple[str, ...]:
        present: list[str] = []
        for name, payload in (
            ("evidence.json", self.evidence),
            ("replay-integrity.json", self.replay_integrity),
            ("command-audit.json", self.command_audit),
            ("safety-transition-audit.json", self.safety_transition_audit),
        ):
            if payload is not None:
                present.append(name)
        present.extend(self.raw_files.keys())
        return tuple(sorted(set(present)))


@dataclass
class LoadedEvidenceBundle:
    """A combined runtime + scenario evidence bundle."""

    runtime: Optional[LoadedRuntimeEvidence] = None
    scenario: Optional[LoadedScenarioEvidence] = None
    warnings: list[LoaderWarning] = field(default_factory=list)

    def all_warnings(self) -> tuple[LoaderWarning, ...]:
        out: list[LoaderWarning] = list(self.warnings)
        if self.runtime is not None:
            out.extend(self.runtime.warnings)
        if self.scenario is not None:
            out.extend(self.scenario.warnings)
        return tuple(out)

    def as_evidence_manifest(self) -> IncidentEvidenceManifest:
        manifest = IncidentEvidenceManifest()
        if self.runtime is not None:
            for name in _RUNTIME_EVIDENCE_FILES:
                path = self.runtime.run_dir / name
                manifest.files[f"runtime/{name}"] = _file_descriptor(
                    path, EvidenceOrigin.RUNTIME_EVIDENCE
                )
        if self.scenario is not None:
            for name in _SCENARIO_EVIDENCE_FILES:
                path = self.scenario.scenario_dir / name
                manifest.files[f"scenario/{name}"] = _file_descriptor(
                    path, EvidenceOrigin.SCENARIO_EVIDENCE
                )
            if self.scenario.run_dir is not None:
                events_path = self.scenario.run_dir / "events.jsonl"
                manifest.files["scenario/events.jsonl"] = _file_descriptor(
                    events_path, EvidenceOrigin.SCENARIO_EVIDENCE
                )
        manifest.warnings.extend(self.all_warnings())
        return manifest


# ---------------------------------------------------------------------------
# Public entry points.
# ---------------------------------------------------------------------------


def load_runtime_evidence(run_dir: Path) -> LoadedRuntimeEvidence:
    """Load every documented file under ``evidence/runtime/<run_id>/``.

    Missing or malformed files become structured warnings.
    """

    run_dir = Path(run_dir)
    loaded = LoadedRuntimeEvidence(run_dir=run_dir, run_id=None)
    if not run_dir.exists():
        loaded.warnings.append(
            LoaderWarning(
                category="missing_directory",
                detail=f"runtime evidence dir does not exist: {run_dir}",
                source=run_dir,
            )
        )
        return loaded
    if not run_dir.is_dir():
        loaded.warnings.append(
            LoaderWarning(
                category="not_a_directory",
                detail=f"expected a directory: {run_dir}",
                source=run_dir,
            )
        )
        return loaded

    json_targets = {
        "runtime-validation.json": "runtime_validation",
        "topic-snapshot.json": "topic_snapshot",
        "node-snapshot.json": "node_snapshot",
        "tf-snapshot.json": "tf_snapshot",
        "command-path-audit.json": "command_path_audit",
        "host-qualification.json": "host_qualification",
        "qualification-summary.json": "qualification_summary",
        "regression-report.json": "regression_report",
    }
    for filename, attr in json_targets.items():
        payload = _load_json(run_dir / filename, loaded.warnings)
        setattr(loaded, attr, payload)

    text_targets = (
        "runtime-validation.md",
        "tf-tree.txt",
        "qualification-summary.md",
        "live-runtime-status.md",
        "known-limitations.md",
    )
    for filename in text_targets:
        text = _load_text(run_dir / filename, loaded.warnings)
        if text is not None:
            loaded.raw_files[filename] = text

    if loaded.runtime_validation:
        loaded.run_id = loaded.runtime_validation.get("run_id") or run_dir.name
    elif loaded.qualification_summary:
        loaded.run_id = loaded.qualification_summary.get("run_id") or run_dir.name
    else:
        loaded.run_id = run_dir.name

    return loaded


def load_scenario_evidence(
    scenario_dir: Path,
    *,
    runs_root: Optional[Path] = None,
) -> LoadedScenarioEvidence:
    """Load every documented file under ``evidence/scenarios/<scenario_id>/``.

    When ``evidence.json`` references a ``runs/<run_id>/`` directory,
    the loader also reads ``events.jsonl`` from that path so the
    timeline builder has rich event records to work with.
    """

    scenario_dir = Path(scenario_dir)
    loaded = LoadedScenarioEvidence(scenario_dir=scenario_dir, scenario_id=None)
    if not scenario_dir.exists():
        loaded.warnings.append(
            LoaderWarning(
                category="missing_directory",
                detail=f"scenario evidence dir does not exist: {scenario_dir}",
                source=scenario_dir,
            )
        )
        return loaded

    json_targets = {
        "evidence.json": "evidence",
        "replay-integrity.json": "replay_integrity",
        "command-audit.json": "command_audit",
        "safety-transition-audit.json": "safety_transition_audit",
    }
    for filename, attr in json_targets.items():
        payload = _load_json(scenario_dir / filename, loaded.warnings)
        setattr(loaded, attr, payload)

    text_targets = ("evidence.md", "events-summary.md")
    for filename in text_targets:
        text = _load_text(scenario_dir / filename, loaded.warnings)
        if text is not None:
            loaded.raw_files[filename] = text

    if loaded.evidence:
        loaded.scenario_id = loaded.evidence.get("scenario_id") or scenario_dir.name
        # Resolve the events stream. The canonical layout ships
        # events.jsonl alongside the scenario summaries (so the
        # scenario evidence directory is self-contained on a fresh
        # checkout). When that file is present, it is the gold
        # source; when it is absent, fall back to the recording
        # directory referenced by evidence.json.
        observed = loaded.evidence.get("observed", {})
        run_dir_raw = observed.get("run_dir") or ""

        local_events_path = scenario_dir / "events.jsonl"
        run_dir: Optional[Path] = None
        events_source: Optional[Path] = None
        if local_events_path.exists():
            events_source = local_events_path
            # The events live in the scenario fixture; the scenario
            # directory is the effective run directory for analysis
            # purposes.
            run_dir = scenario_dir
        elif run_dir_raw:
            candidate = Path(run_dir_raw)
            if candidate.is_absolute() and candidate.exists():
                run_dir = candidate
            elif runs_root is not None:
                run_id = candidate.name
                candidate2 = runs_root / run_id
                if candidate2.exists():
                    run_dir = candidate2
            elif candidate.exists():
                run_dir = candidate
            elif (Path.cwd() / candidate).exists():
                run_dir = Path.cwd() / candidate
            if run_dir is not None:
                events_source = run_dir / "events.jsonl"
        loaded.run_dir = run_dir
        if events_source is not None:
            loaded.events = _load_jsonl(events_source, loaded.warnings)
            if not loaded.events:
                # An empty event stream is a warning, not a failure.
                loaded.warnings.append(
                    LoaderWarning(
                        category="empty_event_stream",
                        detail=(
                            f"events.jsonl produced 0 events for scenario "
                            f"{loaded.scenario_id!r}"
                        ),
                        source=events_source,
                    )
                )
        elif run_dir_raw:
            loaded.warnings.append(
                LoaderWarning(
                    category="missing_run_dir",
                    detail=(
                        f"evidence references run_dir {run_dir_raw!r} but "
                        f"neither {local_events_path.name!r} in the scenario "
                        f"directory nor the recording dir is present"
                    ),
                    source=scenario_dir / "evidence.json",
                )
            )
    else:
        loaded.scenario_id = scenario_dir.name

    return loaded


def load_evidence_bundle(
    *,
    runtime_run_dir: Optional[Path] = None,
    scenario_dir: Optional[Path] = None,
    runs_root: Optional[Path] = None,
) -> LoadedEvidenceBundle:
    """Load a runtime + scenario bundle.

    Either argument may be ``None``. The result records a warning when
    the run id and scenario id disagree (since the user supplied
    cross-referenced inputs).
    """

    bundle = LoadedEvidenceBundle()
    if runtime_run_dir is not None:
        bundle.runtime = load_runtime_evidence(runtime_run_dir)
    if scenario_dir is not None:
        bundle.scenario = load_scenario_evidence(scenario_dir, runs_root=runs_root)
    if bundle.runtime is not None and bundle.scenario is not None:
        run_id = bundle.runtime.run_id
        scenario_run_id = (
            bundle.scenario.evidence.get("observed", {}).get("run_dir", "")
            if bundle.scenario.evidence
            else ""
        )
        if run_id and scenario_run_id and Path(scenario_run_id).name not in {
            run_id,
            (bundle.runtime.runtime_validation or {}).get("run_id", ""),
        }:
            bundle.warnings.append(
                LoaderWarning(
                    category="cross_reference_mismatch",
                    detail=(
                        f"runtime run_id {run_id!r} does not match scenario run_dir "
                        f"{scenario_run_id!r}"
                    ),
                )
            )
    return bundle


# ---------------------------------------------------------------------------
# Internal helpers.
# ---------------------------------------------------------------------------


def _load_json(path: Path, warnings: list[LoaderWarning]) -> Optional[dict]:
    if not path.exists():
        warnings.append(
            LoaderWarning(
                category="missing_file",
                detail=f"file not present: {path.name}",
                source=path,
            )
        )
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        warnings.append(
            LoaderWarning(
                category="unreadable_file",
                detail=f"could not read {path.name}: {exc}",
                source=path,
            )
        )
        return None
    if not text.strip():
        warnings.append(
            LoaderWarning(
                category="empty_file",
                detail=f"{path.name} is empty",
                source=path,
            )
        )
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        warnings.append(
            LoaderWarning(
                category="malformed_json",
                detail=f"{path.name} did not parse: {exc}",
                source=path,
            )
        )
        return None


def _load_text(path: Path, warnings: list[LoaderWarning]) -> Optional[str]:
    if not path.exists():
        warnings.append(
            LoaderWarning(
                category="missing_file",
                detail=f"file not present: {path.name}",
                source=path,
            )
        )
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        warnings.append(
            LoaderWarning(
                category="unreadable_file",
                detail=f"could not read {path.name}: {exc}",
                source=path,
            )
        )
        return None


def _load_jsonl(path: Path, warnings: list[LoaderWarning]) -> list[dict]:
    if not path.exists():
        warnings.append(
            LoaderWarning(
                category="missing_file",
                detail=f"events file not present: {path.name}",
                source=path,
            )
        )
        return []
    out: list[dict] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    warnings.append(
                        LoaderWarning(
                            category="malformed_json",
                            detail=(
                                f"{path.name} line {lineno} did not parse: {exc}"
                            ),
                            source=path,
                        )
                    )
    except OSError as exc:
        warnings.append(
            LoaderWarning(
                category="unreadable_file",
                detail=f"could not read {path.name}: {exc}",
                source=path,
            )
        )
    return out


def _file_descriptor(path: Path, origin: EvidenceOrigin) -> dict:
    if path.exists():
        try:
            size = path.stat().st_size
        except OSError:
            size = -1
        return {
            "origin": origin.value,
            "present": True,
            "size_bytes": size,
            "notes": "",
        }
    return {
        "origin": origin.value,
        "present": False,
        "size_bytes": 0,
        "notes": "file not present",
    }
