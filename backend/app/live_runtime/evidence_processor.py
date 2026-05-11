"""Live runtime evidence processor.

Combines a runner profile, an optional scenario plan, and an optional
bag directory into a single :class:`LiveRuntimeEvidence` record. The
processor enforces the Phase 14 honesty guardrails:

* a record cannot be ``mode=bag_backed`` unless the bag manifest is
  ``BAG_BACKED``;
* a static or missing-bag run cannot be relabelled as
  ``live_runtime``;
* a dry run is always ``mode=dry_run`` and ``status=not_executed``;
* a static-only run is always ``mode=static_only`` and
  ``status=not_executed``;
* an unqualified runner cannot produce a record stronger than
  ``live_runtime_no_bag`` / ``status=partial``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

from app.live_runtime.bag_manifest import (
    BagManifest,
    BagStatus,
    inspect_bag_directory,
)
from app.live_runtime.runner_profile import (
    QualificationOutcome,
    RunnerProfile,
    RunnerStatus,
)
from app.live_runtime.scenario_plan import LiveScenarioPlan
from app.verification.acceptance import AcceptanceStatus


class EvidenceMode(str, Enum):
    BAG_BACKED = "bag_backed"
    LIVE_RUNTIME_NO_BAG = "live_runtime_no_bag"
    DRY_RUN = "dry_run"
    STATIC_ONLY = "static_only"
    NOT_EXECUTED = "not_executed"


@dataclass(frozen=True)
class LiveRuntimeEvidence:
    run_id: str
    generated_at: str
    mode: EvidenceMode
    status: AcceptanceStatus
    reason: str
    bag_manifest: BagManifest
    runner_profile: Optional[RunnerProfile]
    scenario_plan_id: Optional[str]
    expected_evidence_mode: Optional[str]
    required_topics: tuple[str, ...] = ()
    missing_required_topics: tuple[str, ...] = ()
    known_limitations: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_bag_backed(self) -> bool:
        return self.mode is EvidenceMode.BAG_BACKED

    @property
    def is_live_runtime(self) -> bool:
        return self.mode in (
            EvidenceMode.BAG_BACKED,
            EvidenceMode.LIVE_RUNTIME_NO_BAG,
        )

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "mode": self.mode.value,
            "status": self.status.value,
            "reason": self.reason,
            "bag_manifest": self.bag_manifest.as_dict(),
            "runner_profile": (
                self.runner_profile.as_dict() if self.runner_profile else None
            ),
            "scenario_plan_id": self.scenario_plan_id,
            "expected_evidence_mode": self.expected_evidence_mode,
            "required_topics": list(self.required_topics),
            "missing_required_topics": list(self.missing_required_topics),
            "known_limitations": list(self.known_limitations),
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _missing_topics(
    bag_manifest: BagManifest, required: Iterable[str]
) -> tuple[str, ...]:
    if not bag_manifest.topic_inventory:
        # cannot tell what is missing without an inventory
        return tuple(required)
    inv = set(bag_manifest.topic_inventory)
    return tuple(t for t in required if t not in inv)


def process_evidence(
    *,
    run_id: str,
    runner_profile: Optional[RunnerProfile],
    scenario_plan: Optional[LiveScenarioPlan] = None,
    bag_dir: Optional[Path] = None,
    dry_run: bool = False,
    static_only: bool = False,
) -> LiveRuntimeEvidence:
    """Construct the canonical evidence record for a live runtime run.

    The processor never upgrades evidence beyond what the inputs
    justify. The caller is expected to call ``inspect_bag_directory``
    indirectly via this function (or pass an already-classified
    manifest by setting ``bag_dir`` on disk and letting the processor
    classify it).
    """

    if dry_run and static_only:
        raise ValueError("dry_run and static_only are mutually exclusive")

    scenario_plan_id = scenario_plan.plan_id if scenario_plan else None
    expected_mode = (
        scenario_plan.expected_evidence_mode if scenario_plan else None
    )
    required_topics = (
        scenario_plan.required_topics if scenario_plan else ()
    )
    known_limitations: list[str] = []
    generated_at = _now_iso()

    if dry_run:
        bag_manifest = inspect_bag_directory(
            None, scenario_id=scenario_plan_id, run_id=run_id
        )
        bag_manifest = BagManifest(
            bag_dir=None,
            status=BagStatus.NOT_EXECUTED,
            reason="dry-run requested; bag inspection skipped",
            metadata_present=False,
            chunks=(),
            formats=(),
            scenario_id=scenario_plan_id,
            run_id=run_id,
        )
        known_limitations.append("dry-run: no live execution performed")
        return LiveRuntimeEvidence(
            run_id=run_id,
            generated_at=generated_at,
            mode=EvidenceMode.DRY_RUN,
            status=AcceptanceStatus.NOT_EXECUTED,
            reason="dry-run requested",
            bag_manifest=bag_manifest,
            runner_profile=runner_profile,
            scenario_plan_id=scenario_plan_id,
            expected_evidence_mode=expected_mode,
            required_topics=required_topics,
            missing_required_topics=tuple(required_topics),
            known_limitations=tuple(known_limitations),
        )

    if static_only:
        bag_manifest = BagManifest(
            bag_dir=None,
            status=BagStatus.NOT_EXECUTED,
            reason="static-check-only requested; bag inspection skipped",
            metadata_present=False,
            chunks=(),
            formats=(),
            scenario_id=scenario_plan_id,
            run_id=run_id,
        )
        known_limitations.append(
            "static-check-only: no live ROS / Gazebo execution performed"
        )
        return LiveRuntimeEvidence(
            run_id=run_id,
            generated_at=generated_at,
            mode=EvidenceMode.STATIC_ONLY,
            status=AcceptanceStatus.NOT_EXECUTED,
            reason="static-check-only requested",
            bag_manifest=bag_manifest,
            runner_profile=runner_profile,
            scenario_plan_id=scenario_plan_id,
            expected_evidence_mode=expected_mode,
            required_topics=required_topics,
            missing_required_topics=tuple(required_topics),
            known_limitations=tuple(known_limitations),
        )

    bag_manifest = inspect_bag_directory(
        bag_dir, scenario_id=scenario_plan_id, run_id=run_id
    )
    missing_topics = _missing_topics(bag_manifest, required_topics)

    if runner_profile is None:
        known_limitations.append("no runner profile attached to this run")
        return LiveRuntimeEvidence(
            run_id=run_id,
            generated_at=generated_at,
            mode=EvidenceMode.NOT_EXECUTED,
            status=AcceptanceStatus.NOT_EXECUTED,
            reason="no runner profile attached",
            bag_manifest=bag_manifest,
            runner_profile=None,
            scenario_plan_id=scenario_plan_id,
            expected_evidence_mode=expected_mode,
            required_topics=required_topics,
            missing_required_topics=missing_topics,
            known_limitations=tuple(known_limitations),
        )

    if runner_profile.runner_status is RunnerStatus.UNQUALIFIED:
        known_limitations.append(
            f"runner '{runner_profile.runner_id}' is unqualified; "
            "evidence cannot reach bag_backed"
        )
        return LiveRuntimeEvidence(
            run_id=run_id,
            generated_at=generated_at,
            mode=EvidenceMode.NOT_EXECUTED,
            status=AcceptanceStatus.NOT_EXECUTED,
            reason="runner is unqualified",
            bag_manifest=bag_manifest,
            runner_profile=runner_profile,
            scenario_plan_id=scenario_plan_id,
            expected_evidence_mode=expected_mode,
            required_topics=required_topics,
            missing_required_topics=missing_topics,
            known_limitations=tuple(known_limitations),
        )

    if bag_manifest.status is BagStatus.BAG_BACKED:
        if missing_topics:
            return LiveRuntimeEvidence(
                run_id=run_id,
                generated_at=generated_at,
                mode=EvidenceMode.LIVE_RUNTIME_NO_BAG,
                status=AcceptanceStatus.PARTIAL,
                reason=(
                    f"bag present but {len(missing_topics)} required topic(s) "
                    f"missing from bag inventory"
                ),
                bag_manifest=bag_manifest,
                runner_profile=runner_profile,
                scenario_plan_id=scenario_plan_id,
                expected_evidence_mode=expected_mode,
                required_topics=required_topics,
                missing_required_topics=missing_topics,
                known_limitations=tuple(known_limitations),
            )
        return LiveRuntimeEvidence(
            run_id=run_id,
            generated_at=generated_at,
            mode=EvidenceMode.BAG_BACKED,
            status=AcceptanceStatus.PASSED,
            reason="bag-backed live run observed",
            bag_manifest=bag_manifest,
            runner_profile=runner_profile,
            scenario_plan_id=scenario_plan_id,
            expected_evidence_mode=expected_mode,
            required_topics=required_topics,
            missing_required_topics=(),
            known_limitations=tuple(known_limitations),
        )

    if bag_manifest.status in (BagStatus.PARTIAL, BagStatus.INVALID):
        return LiveRuntimeEvidence(
            run_id=run_id,
            generated_at=generated_at,
            mode=EvidenceMode.LIVE_RUNTIME_NO_BAG,
            status=AcceptanceStatus.PARTIAL,
            reason=f"bag classification: {bag_manifest.status.value}",
            bag_manifest=bag_manifest,
            runner_profile=runner_profile,
            scenario_plan_id=scenario_plan_id,
            expected_evidence_mode=expected_mode,
            required_topics=required_topics,
            missing_required_topics=missing_topics,
            known_limitations=tuple(known_limitations),
        )

    # missing_bag and any other classification: never bag-backed.
    return LiveRuntimeEvidence(
        run_id=run_id,
        generated_at=generated_at,
        mode=EvidenceMode.LIVE_RUNTIME_NO_BAG,
        status=AcceptanceStatus.PARTIAL,
        reason="no bag artefacts found; live run cannot be replayed",
        bag_manifest=bag_manifest,
        runner_profile=runner_profile,
        scenario_plan_id=scenario_plan_id,
        expected_evidence_mode=expected_mode,
        required_topics=required_topics,
        missing_required_topics=missing_topics,
        known_limitations=tuple(known_limitations),
    )


def render_evidence_md(evidence: LiveRuntimeEvidence) -> str:
    """Render a short Markdown summary of the evidence record."""

    lines: list[str] = []
    lines.append("# Live Runtime Evidence")
    lines.append("")
    lines.append(
        "_The platform is **not safety-certified**. This document"
        " records one live runtime run on a self-hosted runner._"
    )
    lines.append("")
    lines.append(f"- **Run id:** `{evidence.run_id}`")
    lines.append(f"- **Generated:** {evidence.generated_at}")
    lines.append(f"- **Mode:** `{evidence.mode.value}`")
    lines.append(f"- **Status:** `{evidence.status.value}`")
    lines.append(f"- **Reason:** {evidence.reason}")
    if evidence.scenario_plan_id:
        lines.append(f"- **Scenario plan:** `{evidence.scenario_plan_id}`")
    if evidence.expected_evidence_mode:
        lines.append(
            f"- **Expected mode:** `{evidence.expected_evidence_mode}`"
        )
    if evidence.runner_profile:
        rp = evidence.runner_profile
        lines.append(
            f"- **Runner:** `{rp.runner_id}` "
            f"(status `{rp.runner_status.value}`, "
            f"qualification `{rp.qualification_status.value}`)"
        )
    lines.append("")
    lines.append("## Bag manifest")
    lines.append("")
    bm = evidence.bag_manifest
    lines.append(f"- **Bag dir:** `{bm.bag_dir or 'n/a'}`")
    lines.append(f"- **Status:** `{bm.status.value}`")
    lines.append(f"- **Reason:** {bm.reason}")
    lines.append(f"- **Metadata present:** {bm.metadata_present}")
    lines.append(f"- **Chunks:** {len(bm.chunks)}")
    if bm.formats:
        lines.append(f"- **Formats:** {', '.join(bm.formats)}")
    if bm.topic_inventory:
        lines.append(
            f"- **Topics observed:** {len(bm.topic_inventory)}"
        )
    if evidence.missing_required_topics:
        lines.append("")
        lines.append("## Missing required topics")
        for topic in evidence.missing_required_topics:
            lines.append(f"- `{topic}`")
    if evidence.known_limitations:
        lines.append("")
        lines.append("## Known limitations")
        for note in evidence.known_limitations:
            lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def write_evidence(evidence: LiveRuntimeEvidence, evidence_dir: Path) -> dict:
    """Write evidence.json and evidence.md to ``evidence_dir``.

    Returns a dict with the paths written.
    """

    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    json_path = evidence_dir / "evidence.json"
    md_path = evidence_dir / "evidence.md"
    bag_manifest_path = evidence_dir / "bag-manifest.json"
    json_path.write_text(
        json.dumps(evidence.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_evidence_md(evidence), encoding="utf-8")
    bag_manifest_path.write_text(
        json.dumps(evidence.bag_manifest.as_dict(), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return {
        "evidence_json": str(json_path),
        "evidence_md": str(md_path),
        "bag_manifest_json": str(bag_manifest_path),
    }
