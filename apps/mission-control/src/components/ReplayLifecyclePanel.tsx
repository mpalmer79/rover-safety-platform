import type {
  ArtifactLifecycle,
  ArtifactRegistryRecord,
} from "@/adapters/types";
import { ArtifactIntegrityBadge } from "./ArtifactIntegrityBadge";
import { Panel } from "./Panel";

interface ReplayLifecyclePanelProps {
  record: ArtifactRegistryRecord | null;
}

const LIFECYCLE_RUNGS: ReadonlyArray<ArtifactLifecycle> = [
  "generated",
  "hydrated",
  "committed",
  "verified",
  "canonical",
];

function rungIndex(lifecycle: string): number {
  const idx = LIFECYCLE_RUNGS.indexOf(lifecycle as ArtifactLifecycle);
  return idx;
}

/**
 * Visual ladder of the artifact lifecycle. Every committed artifact
 * advances through ``generated → hydrated → committed → verified →
 * canonical``. The current lifecycle and integrity are surfaced
 * verbatim from the registry; the panel never invents a higher
 * rung than what the registry declares.
 */
export function ReplayLifecyclePanel({ record }: ReplayLifecyclePanelProps) {
  if (!record) {
    return (
      <Panel eyebrow="Replay lifecycle" title="Not registered">
        <p className="body-mono text-base-500">
          No artifact registered for this run. The frontend will
          fall back to the bounded-inputs derivation.
        </p>
      </Panel>
    );
  }
  const idx = rungIndex(record.lifecycle);
  return (
    <Panel
      eyebrow="Replay lifecycle"
      title={record.run_id}
      trailing={
        <ArtifactIntegrityBadge
          integrity={record.integrity}
          lifecycle={record.lifecycle}
        />
      }
    >
      <div data-testid="replay-lifecycle-ladder" className="space-y-2">
        <ol className="flex flex-wrap gap-1.5 text-[11px] font-mono uppercase tracking-wide">
          {LIFECYCLE_RUNGS.map((rung, i) => {
            const reached = idx >= i;
            return (
              <li
                key={rung}
                data-testid={`lifecycle-rung-${rung}`}
                data-reached={reached}
                className={
                  "rounded border px-2 py-1 " +
                  (reached
                    ? "border-accent bg-accent-soft/40 text-accent"
                    : "border-base-300 text-base-500")
                }
              >
                {rung}
              </li>
            );
          })}
          {record.lifecycle === "deprecated" ? (
            <li
              data-testid="lifecycle-rung-deprecated"
              data-reached={true}
              className="rounded border border-status-rejected bg-status-rejected/10 px-2 py-1 text-status-rejected"
            >
              deprecated
            </li>
          ) : null}
        </ol>
        <dl className="grid gap-1 text-[11px] font-mono text-base-700 md:grid-cols-2">
          <div>
            <dt className="text-base-500">derivation_source</dt>
            <dd>{record.derivation_source}</dd>
          </div>
          <div>
            <dt className="text-base-500">bag_status</dt>
            <dd>{record.bag_status}</dd>
          </div>
          <div>
            <dt className="text-base-500">mission</dt>
            <dd>{record.related_mission_id || "—"}</dd>
          </div>
          <div>
            <dt className="text-base-500">scenario</dt>
            <dd>{record.related_scenario_id || "—"}</dd>
          </div>
        </dl>
        {record.notes.length > 0 ? (
          <ul className="mt-1 space-y-0.5 text-[11px] text-base-600">
            {record.notes.map((n) => (
              <li key={n}>• {n}</li>
            ))}
          </ul>
        ) : null}
      </div>
    </Panel>
  );
}
