import { loadRehearsalAudits } from "@/adapters/loader";
import { MissionCard } from "@/components/MissionCard";
import { Panel } from "@/components/Panel";
import { PageSurface } from "@/components/PageSurface";

export const dynamic = "force-static";

export default async function ReplayIndexPage() {
  const audits = await loadRehearsalAudits();
  const sorted = [...audits].sort((a, b) => {
    if (a.final_status === b.final_status) {
      return a.request.mission_id.localeCompare(b.request.mission_id);
    }
    return a.final_status.localeCompare(b.final_status);
  });
  return (
    <PageSurface>
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="label">Replay viewer</p>
        <h1 className="display-1">Rehearsal replay index</h1>
        <p className="text-base-700">
          All committed rehearsal audits. Pick a row to inspect its
          deterministic event stream, supervisor decision, replay
          markers, and analytics.
        </p>
      </header>

      <Panel
        eyebrow="Rehearsals"
        title={`${sorted.length} audit bundles`}
        trailing={
          <span className="text-xs text-base-500">
            simulation-only · bag-backed: 0
          </span>
        }
      >
        <div className="grid gap-3 lg:grid-cols-2">
          {sorted.map((audit) => (
            <MissionCard key={audit.request.mission_id} audit={audit} />
          ))}
        </div>
      </Panel>
    </div>
    </PageSurface>
  );
}
