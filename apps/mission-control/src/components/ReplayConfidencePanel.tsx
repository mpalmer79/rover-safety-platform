import type {
  ArtifactRegistryRecord,
  SpatialReplayArtifact,
} from "@/adapters/types";
import { describeDerivationSource } from "@/adapters/spatial";
import { Panel } from "./Panel";
import { SpatialReplayBadge } from "./SpatialReplayBadge";

interface ReplayConfidencePanelProps {
  artifact: SpatialReplayArtifact | null;
  record: ArtifactRegistryRecord | null;
}

/**
 * Confidence indicator for the active spatial-replay artefact.
 *
 * Confidence is computed from THREE inputs (in this order):
 *
 *   1. derivation_source — fixture < bounded_inputs < bag_backed
 *   2. validation_status — failed < not_executed < partial < passed
 *   3. registry integrity — missing/failed < partial < passed
 *
 * The panel never overrides any of these; it merely surfaces them
 * in one place so the operator can read the trust level at a
 * glance. ``Confidence`` is a textual band, not a numeric score.
 */
export function ReplayConfidencePanel({
  artifact,
  record,
}: ReplayConfidencePanelProps) {
  if (!artifact) {
    return (
      <Panel eyebrow="Replay confidence" title="No artefact">
        <p className="body-mono text-base-500">
          No spatial-replay artefact for this run; the playback panel
          falls back to the bounded-inputs derivation.
        </p>
      </Panel>
    );
  }
  const band = computeConfidenceBand(artifact, record);
  return (
    <Panel
      eyebrow="Replay confidence"
      title={artifact.run_id}
      trailing={<SpatialReplayBadge source={artifact.derivation_source} />}
    >
      <div className="space-y-2 text-[12px]">
        <div
          data-testid="replay-confidence-band"
          data-band={band.tier}
          className={
            "inline-flex items-center gap-2 rounded border px-2 py-1 font-mono uppercase tracking-wide " +
            BAND_TONE[band.tier]
          }
        >
          <span aria-hidden>◆</span>
          <span>confidence: {band.label}</span>
        </div>
        <p className="text-base-700">{band.rationale}</p>
        <dl className="grid gap-1 text-[11px] font-mono text-base-700 md:grid-cols-2">
          <div>
            <dt className="text-base-500">derivation_source</dt>
            <dd>{describeDerivationSource(artifact.derivation_source)}</dd>
          </div>
          <div>
            <dt className="text-base-500">bag_status</dt>
            <dd>{artifact.bag_status}</dd>
          </div>
          <div>
            <dt className="text-base-500">validation_status</dt>
            <dd>{artifact.validation_status}</dd>
          </div>
          <div>
            <dt className="text-base-500">registry integrity</dt>
            <dd>{record?.integrity ?? "unregistered"}</dd>
          </div>
          <div>
            <dt className="text-base-500">samples</dt>
            <dd>{artifact.sample_count}</dd>
          </div>
          <div>
            <dt className="text-base-500">topic sources</dt>
            <dd>{artifact.topic_sources.join(", ") || "—"}</dd>
          </div>
        </dl>
        {artifact.missing_topics.length > 0 ? (
          <p className="text-[11px] text-status-pending">
            Missing topics: {artifact.missing_topics.join(", ")}
          </p>
        ) : null}
      </div>
    </Panel>
  );
}

const BAND_TONE: Record<string, string> = {
  high: "border-status-completed text-status-completed",
  medium: "border-status-pending text-status-pending",
  low: "border-status-rejected text-status-rejected",
  unavailable: "border-base-400 text-base-600",
};

interface ConfidenceBand {
  tier: "high" | "medium" | "low" | "unavailable";
  label: string;
  rationale: string;
}

function computeConfidenceBand(
  artifact: SpatialReplayArtifact,
  record: ArtifactRegistryRecord | null,
): ConfidenceBand {
  const integrity = record?.integrity ?? "unverified";
  if (artifact.derivation_source === "unavailable") {
    return {
      tier: "unavailable",
      label: "unavailable",
      rationale: "No spatial samples; UI falls back to bounded inputs.",
    };
  }
  if (
    artifact.derivation_source === "bag_backed" &&
    artifact.validation_status === "passed" &&
    integrity === "passed"
  ) {
    return {
      tier: "high",
      label: "high · bag-backed",
      rationale: "Bag-backed pose samples; validator + registry integrity passed.",
    };
  }
  if (
    artifact.derivation_source === "fixture" &&
    artifact.validation_status === "passed" &&
    integrity === "passed"
  ) {
    return {
      tier: "medium",
      label: "medium · fixture",
      rationale:
        "Fixture-derived spatial samples; not bag-backed evidence. Hashes verified.",
    };
  }
  if (
    artifact.validation_status === "partial" ||
    integrity === "partial"
  ) {
    return {
      tier: "low",
      label: "low · partial",
      rationale:
        "Partial validation or integrity drift; review the missing topics + drift list.",
    };
  }
  if (integrity === "failed" || artifact.validation_status === "failed") {
    return {
      tier: "low",
      label: "low · failed",
      rationale:
        "Validation or integrity failed; the playback panel will fall back to bounded inputs.",
    };
  }
  return {
    tier: "medium",
    label: "medium",
    rationale:
      "Spatial samples present but the integrity / validator state is mixed.",
  };
}
