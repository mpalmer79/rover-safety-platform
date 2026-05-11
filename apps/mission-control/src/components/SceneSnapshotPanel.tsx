import type {
  ArtifactRegistryRecord,
  SpatialReplayArtifact,
} from "@/adapters/types";
import { computeSceneSnapshot, type SceneSnapshotStatus } from "@/adapters/sceneSnapshot";
import { Panel } from "./Panel";

interface SceneSnapshotPanelProps {
  runId: string;
  artifact: SpatialReplayArtifact | null;
  record: ArtifactRegistryRecord | null;
}

const STATUS_TONE: Record<SceneSnapshotStatus, string> = {
  bag_backed: "border-[color:var(--mc-status-completed)] text-[color:var(--mc-status-completed)]",
  fixture: "border-[color:var(--mc-status-pending)] text-[color:var(--mc-status-pending)]",
  not_executed: "border-[color:var(--mc-status-warning)] text-[color:var(--mc-status-warning)]",
  unavailable: "border-[color:var(--mc-status-rejected)] text-[color:var(--mc-status-rejected)]",
};

const STATUS_LABEL: Record<SceneSnapshotStatus, string> = {
  bag_backed: "Eligible · bag-backed",
  fixture: "Fixture-only · not bag-backed",
  not_executed: "Not executed · missing inputs",
  unavailable: "Unavailable · no artefact",
};

/**
 * Reviewer scene-snapshot readiness panel.
 *
 * Surfaces whether a bag-backed reviewer snapshot COULD be
 * produced for this run, and lists the missing inputs if not. The
 * panel never claims a snapshot exists; the only way the
 * "reviewer_export_ready" flag becomes true is if the artefact
 * registry, spatial-replay, and bag-status all align.
 */
export function SceneSnapshotPanel({
  runId,
  artifact,
  record,
}: SceneSnapshotPanelProps) {
  const state = computeSceneSnapshot(runId, artifact, record);
  const tone = STATUS_TONE[state.status];

  return (
    <Panel
      eyebrow="Reviewer scene snapshot"
      title={state.run_id}
      trailing={
        <span
          data-testid="scene-snapshot-status"
          data-status={state.status}
          data-export-ready={state.reviewer_export_ready}
          className={
            "inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[11px] font-mono uppercase tracking-wide " +
            tone
          }
        >
          {STATUS_LABEL[state.status]}
        </span>
      }
    >
      <div className="space-y-3 text-[12px]">
        <dl className="grid gap-1 font-mono text-[11px] md:grid-cols-2">
          <div>
            <dt className="label">derivation_source</dt>
            <dd className="text-[color:var(--mc-text)]">
              {state.derivation_source || "—"}
            </dd>
          </div>
          <div>
            <dt className="label">bag_status</dt>
            <dd className="text-[color:var(--mc-text)]">
              {state.bag_status || "—"}
            </dd>
          </div>
          <div>
            <dt className="label">registry integrity</dt>
            <dd className="text-[color:var(--mc-text)]">{state.integrity}</dd>
          </div>
          <div>
            <dt className="label">reviewer export ready</dt>
            <dd
              data-testid="scene-snapshot-export-ready"
              className="text-[color:var(--mc-text)]"
            >
              {state.reviewer_export_ready ? "yes" : "no"}
            </dd>
          </div>
        </dl>

        {state.missing_inputs.length > 0 ? (
          <div>
            <p className="label mb-1">Missing inputs</p>
            <ul
              data-testid="scene-snapshot-missing"
              className="space-y-0.5 text-[11px] text-muted"
            >
              {state.missing_inputs.map((m) => (
                <li key={m}>• {m}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {state.artifact_hash_chain.length > 0 ? (
          <div>
            <p className="label mb-1">Artefact hash chain</p>
            <ul
              data-testid="scene-snapshot-hash-chain"
              className="space-y-0.5 font-mono text-[11px] text-muted"
            >
              {state.artifact_hash_chain.map((c) => (
                <li key={c.relative_path}>
                  <span className="text-[color:var(--mc-text)]">{c.sha256_prefix}</span>
                  <span className="ml-2">{c.relative_path}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {state.notes.length > 0 ? (
          <p data-testid="scene-snapshot-notes" className="text-[11px] text-muted">
            {state.notes.join(" ")}
          </p>
        ) : null}
      </div>
    </Panel>
  );
}
