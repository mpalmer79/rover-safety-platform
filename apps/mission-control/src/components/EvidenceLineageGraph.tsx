import type {
  ArtifactRegistryRecord,
  SpatialReplayArtifact,
} from "@/adapters/types";
import { describeDerivationSource } from "@/adapters/spatial";
import { Panel } from "./Panel";

interface EvidenceLineageGraphProps {
  artifact: SpatialReplayArtifact | null;
  record: ArtifactRegistryRecord | null;
}

/**
 * Lineage chain for one mission's spatial evidence.
 *
 * The chain is rendered as a simple ordered list of nodes: every
 * node names a verbatim source string (rehearsal audit, bag
 * manifest, fixture, registry). The graph's only job is to make
 * the *origin of the data* legible to a reviewer.
 */
export function EvidenceLineageGraph({
  artifact,
  record,
}: EvidenceLineageGraphProps) {
  const nodes = buildLineageNodes(artifact, record);
  if (nodes.length === 0) {
    return (
      <Panel eyebrow="Evidence lineage" title="No evidence">
        <p className="body-mono text-base-500">
          No spatial-replay artifact for this run; nothing to graph.
        </p>
      </Panel>
    );
  }
  return (
    <Panel
      eyebrow="Evidence lineage"
      title="Source-to-render chain"
    >
      <ol
        data-testid="evidence-lineage-graph"
        className="space-y-2 text-[12px]"
      >
        {nodes.map((node, idx) => (
          <li
            key={node.id}
            data-testid={`evidence-lineage-node-${idx}`}
            className={
              "flex items-start gap-3 rounded border border-base-200 bg-base-100 px-3 py-2 " +
              (node.tone === "warn"
                ? "border-status-pending"
                : node.tone === "fail"
                  ? "border-status-rejected"
                  : "")
            }
          >
            <span className="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-accent-soft/40 text-[11px] font-mono text-accent">
              {idx + 1}
            </span>
            <div className="flex-1">
              <p className="font-mono text-[11px] uppercase tracking-wide text-base-500">
                {node.eyebrow}
              </p>
              <p className="text-base-800">{node.title}</p>
              {node.detail ? (
                <p className="mt-0.5 text-[11px] text-base-600">{node.detail}</p>
              ) : null}
            </div>
          </li>
        ))}
      </ol>
    </Panel>
  );
}

interface LineageNode {
  id: string;
  eyebrow: string;
  title: string;
  detail?: string;
  tone?: "ok" | "warn" | "fail";
}

function buildLineageNodes(
  artifact: SpatialReplayArtifact | null,
  record: ArtifactRegistryRecord | null,
): LineageNode[] {
  if (!artifact) return [];
  const nodes: LineageNode[] = [];
  if (record?.related_mission_id) {
    nodes.push({
      id: "rehearsal",
      eyebrow: "rehearsal audit",
      title: `mission-rehearsals/audits/${record.related_mission_id}/`,
      detail:
        "Deterministic rehearsal events + plan; sourced from the Phase 16 pipeline.",
      tone: "ok",
    });
  }
  if (artifact.derivation_source === "bag_backed") {
    nodes.push({
      id: "bag-manifest",
      eyebrow: "bag manifest",
      title: "evidence/runtime/<run_id>/bag-manifest.json",
      detail: `Validation: ${artifact.validation_status}; topics: ${artifact.topic_sources.join(", ")}.`,
      tone: artifact.validation_status === "passed" ? "ok" : "warn",
    });
    nodes.push({
      id: "pose-samples",
      eyebrow: "pose samples (operator post-processed)",
      title: "evidence/runtime/<run_id>/pose-samples.jsonl",
      detail: `${artifact.sample_count} samples; never invented by the platform.`,
      tone: "ok",
    });
  } else if (artifact.derivation_source === "fixture") {
    nodes.push({
      id: "fixture",
      eyebrow: "committed fixture",
      title: `spatial-replay/fixtures/${artifact.run_id}/pose-samples.jsonl`,
      detail: "Hand-authored fixture; not bag-backed evidence.",
      tone: "warn",
    });
  } else {
    nodes.push({
      id: "bounded-inputs",
      eyebrow: "bounded inputs",
      title: "mission-rehearsals/audits/<id>/mission-plan.json",
      detail:
        "Bounded distance/angle inputs; the spatial layer derives a deterministic 2D layout.",
      tone: "ok",
    });
  }
  nodes.push({
    id: "spatial-replay",
    eyebrow: "spatial-replay artifact",
    title: `spatial-replay/runs/${artifact.run_id}/spatial-replay.json`,
    detail: `derivation_source = ${artifact.derivation_source}; bag_status = ${artifact.bag_status}.`,
    tone: artifact.derivation_source === "bag_backed" ? "ok" : "warn",
  });
  if (record) {
    nodes.push({
      id: "registry",
      eyebrow: "canonical artifact registry",
      title: "spatial-replay/registry/canonical-artifacts.json",
      detail: `lifecycle = ${record.lifecycle}; integrity = ${record.integrity}; ${record.files.length} files indexed.`,
      tone:
        record.integrity === "failed" || record.integrity === "missing"
          ? "fail"
          : record.integrity === "partial"
            ? "warn"
            : "ok",
    });
  }
  nodes.push({
    id: "render",
    eyebrow: "render",
    title: describeDerivationSource(artifact.derivation_source),
    detail: "Caption + badge are the only surfaces that name the source.",
  });
  return nodes;
}
