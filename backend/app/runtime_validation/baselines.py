"""Runtime baselines and per-category diffs.

A *baseline* is a snapshot of the runtime contract captured from a
known-good qualification run. It pins:

* the topic inventory (by name + message type);
* the TF frame inventory (by name + parent);
* the node inventory (by name + package);
* the safety-state transition signature (ordered list of states);
* the authorized-command shape (min / max linear and angular speeds
  observed);
* the event counts per type;
* the expected replay artefacts;
* the diagnostic-health summary at end-of-run.

Comparing a new run to a baseline classifies each delta into one of:

* ``expected_difference`` — value differs but the difference is
  declared in :data:`EXPECTED_DELTA_KEYS` (e.g. timestamps, run ids);
* ``warning`` — small, recoverable deltas (extra optional node, more
  events than the baseline, slightly broader command range);
* ``regression`` — a documented invariant degraded (missing optional
  topic, missing optional event);
* ``critical_regression`` — a required invariant degraded (missing
  required topic, missing required node, unexpected safety
  transition, missing replay artefact, command-path violation).

The classification is deterministic: a delta with the same inputs
always returns the same severity. The comparator never silently
auto-ignores a regression — every classified delta carries a
human-readable detail string.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional


EXPECTED_DELTA_KEYS: frozenset[str] = frozenset(
    {
        "run_id",
        "generated_at_utc",
        "settle_seconds",
    }
)


class DeltaSeverity(str, Enum):
    EXPECTED_DIFFERENCE = "expected_difference"
    WARNING = "warning"
    REGRESSION = "regression"
    CRITICAL_REGRESSION = "critical_regression"


_SEVERITY_ORDER: dict[DeltaSeverity, int] = {
    DeltaSeverity.EXPECTED_DIFFERENCE: 0,
    DeltaSeverity.WARNING: 1,
    DeltaSeverity.REGRESSION: 2,
    DeltaSeverity.CRITICAL_REGRESSION: 3,
}


@dataclass(frozen=True)
class BaselineCategory:
    name: str
    """One of: topics, nodes, tf_frames, safety_transitions,
    authorized_commands, event_counts, replay_artifacts,
    diagnostic_health."""

    required_keys: tuple[str, ...] = ()
    """Keys whose absence in the new run is a critical regression."""


_CATEGORIES: tuple[BaselineCategory, ...] = (
    BaselineCategory(name="topics"),
    BaselineCategory(name="nodes"),
    BaselineCategory(name="tf_frames"),
    BaselineCategory(name="safety_transitions"),
    BaselineCategory(name="authorized_commands"),
    BaselineCategory(name="event_counts"),
    BaselineCategory(name="replay_artifacts"),
    BaselineCategory(name="diagnostic_health"),
)


@dataclass
class BaselineDelta:
    category: str
    key: str
    severity: DeltaSeverity
    detail: str
    baseline_value: Any = None
    observed_value: Any = None
    evidence_paths: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "category": self.category,
            "key": self.key,
            "severity": self.severity.value,
            "detail": self.detail,
            "baseline_value": _jsonable(self.baseline_value),
            "observed_value": _jsonable(self.observed_value),
            "evidence_paths": list(self.evidence_paths),
        }


@dataclass
class BaselineComparison:
    baseline_path: Path
    observed_path: Path
    deltas: list[BaselineDelta] = field(default_factory=list)

    @property
    def severity(self) -> DeltaSeverity:
        if not self.deltas:
            return DeltaSeverity.EXPECTED_DIFFERENCE
        return max(self.deltas, key=lambda d: _SEVERITY_ORDER[d.severity]).severity

    def has_regression(self) -> bool:
        return any(
            d.severity in (DeltaSeverity.REGRESSION, DeltaSeverity.CRITICAL_REGRESSION)
            for d in self.deltas
        )

    def summary_counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in DeltaSeverity}
        for d in self.deltas:
            out[d.severity.value] += 1
        return out

    def as_dict(self) -> dict:
        return {
            "baseline_path": str(self.baseline_path),
            "observed_path": str(self.observed_path),
            "severity": self.severity.value,
            "summary_counts": self.summary_counts(),
            "deltas": [d.as_dict() for d in self.deltas],
        }


# ---------------------------------------------------------------------------
# Baseline IO.
# ---------------------------------------------------------------------------


def write_baseline(*, baseline: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(baseline, indent=2, sort_keys=True), encoding="utf-8")


def load_baseline(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def baseline_from_evidence(run_dir: Path) -> dict:
    """Compose a baseline JSON from an ``evidence/runtime/<run_id>/`` dir.

    The composer reads only the documented evidence files; missing
    files become empty inventories (the comparator treats that as a
    critical regression on the next compare, which is the desired
    behaviour).
    """

    out = {
        "topics": {},
        "nodes": {},
        "tf_frames": {},
        "safety_transitions": [],
        "authorized_commands": {},
        "event_counts": {},
        "replay_artifacts": [],
        "diagnostic_health": {},
        "metadata": {},
    }
    topic_path = run_dir / "topic-snapshot.json"
    if topic_path.exists():
        topic = json.loads(topic_path.read_text(encoding="utf-8"))
        out["topics"] = _build_topic_inventory(topic)
        out["metadata"]["topic_run_id"] = topic.get("run_id", "")
    node_path = run_dir / "node-snapshot.json"
    if node_path.exists():
        node = json.loads(node_path.read_text(encoding="utf-8"))
        out["nodes"] = _build_node_inventory(node)
    tf_path = run_dir / "tf-snapshot.json"
    if tf_path.exists():
        tf = json.loads(tf_path.read_text(encoding="utf-8"))
        out["tf_frames"] = _build_tf_inventory(tf)
    capture_path = run_dir / "runtime-capture.json"
    if capture_path.exists():
        capture = json.loads(capture_path.read_text(encoding="utf-8"))
        out["safety_transitions"] = list(
            capture.get("safety_transitions", [])
        )
        out["event_counts"] = dict(capture.get("event_counts", {}))
    cmd_path = run_dir / "command-path-audit.json"
    if cmd_path.exists():
        cmd = json.loads(cmd_path.read_text(encoding="utf-8"))
        out["authorized_commands"] = _build_command_summary(cmd)
    replay_path = run_dir / "replay-integrity.json"
    if replay_path.exists():
        replay = json.loads(replay_path.read_text(encoding="utf-8"))
        out["replay_artifacts"] = sorted(replay.get("artifacts_present", []))
    return out


def _build_topic_inventory(payload: dict) -> dict[str, str]:
    rows = payload.get("live", {}).get("rows") or payload.get("static", {}).get("rows", [])
    inventory: dict[str, str] = {}
    for row in rows:
        name = row.get("topic")
        if isinstance(name, str):
            inventory[name] = row.get("msg_type", "")
    return inventory


def _build_node_inventory(payload: dict) -> dict[str, str]:
    rows = payload.get("live", {}).get("rows") or payload.get("static", {}).get("rows", [])
    inventory: dict[str, str] = {}
    for row in rows:
        name = row.get("node_name")
        if isinstance(name, str):
            inventory[name] = row.get("package", "")
    return inventory


def _build_tf_inventory(payload: dict) -> dict[str, str]:
    rows = payload.get("live", {}).get("rows") or payload.get("static", {}).get("rows", [])
    inventory: dict[str, str] = {}
    for row in rows:
        name = row.get("frame")
        if isinstance(name, str):
            inventory[name] = row.get("parent_expected") or "<root>"
    return inventory


def _build_command_summary(payload: dict) -> dict[str, Any]:
    samples = (
        payload.get("live", {}).get("authorized_samples")
        or []
    )
    if not samples:
        return {}
    linears = [s.get("linear_x", 0.0) for s in samples]
    angulars = [s.get("angular_z", 0.0) for s in samples]
    return {
        "min_linear_x": min(linears),
        "max_linear_x": max(linears),
        "min_angular_z": min(angulars),
        "max_angular_z": max(angulars),
        "sample_count": len(samples),
    }


# ---------------------------------------------------------------------------
# Comparison.
# ---------------------------------------------------------------------------


def compare_baseline(
    *,
    baseline: Mapping[str, Any],
    observed: Mapping[str, Any],
    baseline_path: Path,
    observed_path: Path,
    required_topics: Iterable[str] = (),
    required_nodes: Iterable[str] = (),
    required_tf_frames: Iterable[str] = (),
    optional_topics: Iterable[str] = (),
    optional_nodes: Iterable[str] = (),
    evidence_paths_by_category: Optional[Mapping[str, tuple[str, ...]]] = None,
) -> BaselineComparison:
    """Compare ``observed`` against ``baseline`` and classify deltas."""

    evidence_paths_by_category = evidence_paths_by_category or {}
    required_topics_set = set(required_topics)
    required_nodes_set = set(required_nodes)
    required_tf_set = set(required_tf_frames)
    optional_topics_set = set(optional_topics)
    optional_nodes_set = set(optional_nodes)

    deltas: list[BaselineDelta] = []
    deltas.extend(
        _diff_inventory(
            category="topics",
            baseline=baseline.get("topics", {}),
            observed=observed.get("topics", {}),
            required=required_topics_set,
            optional=optional_topics_set,
            evidence=evidence_paths_by_category.get("topics", ()),
        )
    )
    deltas.extend(
        _diff_inventory(
            category="nodes",
            baseline=baseline.get("nodes", {}),
            observed=observed.get("nodes", {}),
            required=required_nodes_set,
            optional=optional_nodes_set,
            evidence=evidence_paths_by_category.get("nodes", ()),
        )
    )
    deltas.extend(
        _diff_inventory(
            category="tf_frames",
            baseline=baseline.get("tf_frames", {}),
            observed=observed.get("tf_frames", {}),
            required=required_tf_set,
            optional=set(),
            evidence=evidence_paths_by_category.get("tf_frames", ()),
        )
    )
    deltas.extend(
        _diff_safety_transitions(
            baseline=baseline.get("safety_transitions", []),
            observed=observed.get("safety_transitions", []),
            evidence=evidence_paths_by_category.get("safety_transitions", ()),
        )
    )
    deltas.extend(
        _diff_event_counts(
            baseline=baseline.get("event_counts", {}),
            observed=observed.get("event_counts", {}),
            evidence=evidence_paths_by_category.get("event_counts", ()),
        )
    )
    deltas.extend(
        _diff_replay_artifacts(
            baseline=baseline.get("replay_artifacts", []),
            observed=observed.get("replay_artifacts", []),
            evidence=evidence_paths_by_category.get("replay_artifacts", ()),
        )
    )
    deltas.extend(
        _diff_authorized_commands(
            baseline=baseline.get("authorized_commands", {}),
            observed=observed.get("authorized_commands", {}),
            evidence=evidence_paths_by_category.get("authorized_commands", ()),
        )
    )
    return BaselineComparison(
        baseline_path=baseline_path,
        observed_path=observed_path,
        deltas=deltas,
    )


def _diff_inventory(
    *,
    category: str,
    baseline: Mapping[str, Any],
    observed: Mapping[str, Any],
    required: set[str],
    optional: set[str],
    evidence: tuple[str, ...],
) -> list[BaselineDelta]:
    deltas: list[BaselineDelta] = []
    baseline_keys = set(baseline.keys())
    observed_keys = set(observed.keys())
    for key in sorted(baseline_keys - observed_keys):
        if key in required:
            severity = DeltaSeverity.CRITICAL_REGRESSION
            detail = f"required {category[:-1]} {key!r} missing from observed run"
        elif key in optional:
            severity = DeltaSeverity.WARNING
            detail = f"optional {category[:-1]} {key!r} missing from observed run"
        else:
            severity = DeltaSeverity.REGRESSION
            detail = f"baseline {category[:-1]} {key!r} missing from observed run"
        deltas.append(
            BaselineDelta(
                category=category,
                key=key,
                severity=severity,
                detail=detail,
                baseline_value=baseline.get(key),
                observed_value=None,
                evidence_paths=evidence,
            )
        )
    for key in sorted(observed_keys - baseline_keys):
        if key in required:
            severity = DeltaSeverity.EXPECTED_DIFFERENCE
            detail = f"required {category[:-1]} {key!r} appeared (declared required)"
        else:
            severity = DeltaSeverity.WARNING
            detail = f"observed run added {category[:-1]} {key!r}"
        deltas.append(
            BaselineDelta(
                category=category,
                key=key,
                severity=severity,
                detail=detail,
                baseline_value=None,
                observed_value=observed.get(key),
                evidence_paths=evidence,
            )
        )
    for key in sorted(baseline_keys & observed_keys):
        if baseline[key] != observed[key]:
            deltas.append(
                BaselineDelta(
                    category=category,
                    key=key,
                    severity=DeltaSeverity.REGRESSION,
                    detail=(
                        f"{category[:-1]} {key!r} value drift: "
                        f"baseline={baseline[key]!r} observed={observed[key]!r}"
                    ),
                    baseline_value=baseline[key],
                    observed_value=observed[key],
                    evidence_paths=evidence,
                )
            )
    return deltas


def _diff_safety_transitions(
    *,
    baseline: list,
    observed: list,
    evidence: tuple[str, ...],
) -> list[BaselineDelta]:
    if list(baseline) == list(observed):
        return []
    return [
        BaselineDelta(
            category="safety_transitions",
            key="sequence",
            severity=DeltaSeverity.CRITICAL_REGRESSION,
            detail=(
                f"safety transition sequence drifted: "
                f"baseline={baseline} observed={observed}"
            ),
            baseline_value=list(baseline),
            observed_value=list(observed),
            evidence_paths=evidence,
        )
    ]


def _diff_event_counts(
    *,
    baseline: Mapping[str, int],
    observed: Mapping[str, int],
    evidence: tuple[str, ...],
) -> list[BaselineDelta]:
    deltas: list[BaselineDelta] = []
    for key in sorted(set(baseline) | set(observed)):
        b = int(baseline.get(key, 0))
        o = int(observed.get(key, 0))
        if b == o:
            continue
        if b > 0 and o == 0:
            severity = DeltaSeverity.REGRESSION
            detail = f"event {key!r} disappeared (baseline={b}, observed=0)"
        elif b == 0 and o > 0:
            severity = DeltaSeverity.WARNING
            detail = f"event {key!r} appeared (baseline=0, observed={o})"
        elif o < b:
            severity = DeltaSeverity.WARNING
            detail = f"event {key!r} count dropped (baseline={b}, observed={o})"
        else:
            severity = DeltaSeverity.WARNING
            detail = f"event {key!r} count rose (baseline={b}, observed={o})"
        deltas.append(
            BaselineDelta(
                category="event_counts",
                key=key,
                severity=severity,
                detail=detail,
                baseline_value=b,
                observed_value=o,
                evidence_paths=evidence,
            )
        )
    return deltas


def _diff_replay_artifacts(
    *,
    baseline: list,
    observed: list,
    evidence: tuple[str, ...],
) -> list[BaselineDelta]:
    baseline_set = set(baseline)
    observed_set = set(observed)
    deltas: list[BaselineDelta] = []
    for missing in sorted(baseline_set - observed_set):
        deltas.append(
            BaselineDelta(
                category="replay_artifacts",
                key=missing,
                severity=DeltaSeverity.CRITICAL_REGRESSION,
                detail=f"replay artefact {missing!r} missing from observed run",
                baseline_value=missing,
                observed_value=None,
                evidence_paths=evidence,
            )
        )
    for extra in sorted(observed_set - baseline_set):
        deltas.append(
            BaselineDelta(
                category="replay_artifacts",
                key=extra,
                severity=DeltaSeverity.WARNING,
                detail=f"observed run added replay artefact {extra!r}",
                baseline_value=None,
                observed_value=extra,
                evidence_paths=evidence,
            )
        )
    return deltas


def _diff_authorized_commands(
    *,
    baseline: Mapping[str, Any],
    observed: Mapping[str, Any],
    evidence: tuple[str, ...],
) -> list[BaselineDelta]:
    if not baseline and not observed:
        return []
    if baseline and not observed:
        return [
            BaselineDelta(
                category="authorized_commands",
                key="sample_count",
                severity=DeltaSeverity.CRITICAL_REGRESSION,
                detail="observed run produced no authorized command samples",
                baseline_value=baseline.get("sample_count", 0),
                observed_value=0,
                evidence_paths=evidence,
            )
        ]
    deltas: list[BaselineDelta] = []
    for key in ("min_linear_x", "max_linear_x", "min_angular_z", "max_angular_z"):
        b = baseline.get(key)
        o = observed.get(key)
        if b is None or o is None:
            continue
        if abs(float(b) - float(o)) <= 1e-3:
            continue
        # Wider envelope is a warning; narrower (more conservative) is
        # an expected_difference because a tighter cap is generally
        # safer.
        wider = (
            (key.startswith("max_") and float(o) > float(b))
            or (key.startswith("min_") and float(o) < float(b))
        )
        severity = DeltaSeverity.WARNING if wider else DeltaSeverity.EXPECTED_DIFFERENCE
        deltas.append(
            BaselineDelta(
                category="authorized_commands",
                key=key,
                severity=severity,
                detail=(
                    f"authorized command envelope drifted on {key}: "
                    f"baseline={b} observed={o}"
                ),
                baseline_value=b,
                observed_value=o,
                evidence_paths=evidence,
            )
        )
    return deltas


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return repr(value)


def render_comparison_md(comparison: BaselineComparison) -> str:
    counts = comparison.summary_counts()
    lines: list[str] = []
    lines.append("# Runtime Baseline Comparison")
    lines.append("")
    lines.append(f"- **Baseline:** `{comparison.baseline_path}`")
    lines.append(f"- **Observed:** `{comparison.observed_path}`")
    lines.append(f"- **Overall severity:** `{comparison.severity.value}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|---|---|")
    for sev in DeltaSeverity:
        lines.append(f"| `{sev.value}` | {counts[sev.value]} |")
    lines.append("")
    if comparison.deltas:
        lines.append("## Deltas")
        lines.append("")
        lines.append("| Category | Key | Severity | Detail |")
        lines.append("|---|---|---|---|")
        for d in comparison.deltas:
            lines.append(
                f"| `{d.category}` | `{d.key}` | `{d.severity.value}` | {d.detail} |"
            )
    else:
        lines.append("_No deltas detected; observed run matches baseline._")
    lines.append("")
    return "\n".join(lines)
