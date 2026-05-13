import Link from "next/link";
import { PlayCircle } from "lucide-react";

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
          The replay viewer reconstructs simulated mission outcomes
          from deterministic event artifacts. Pick a row to inspect a
          mission's event stream, supervisor decision, replay markers,
          and analytics.
        </p>
      </header>

      <Panel
        eyebrow="What this proves"
        title="Reviewer summary"
        trailing={
          <Link
            href="/demo/warehouse-replay"
            data-testid="replay-index-demo-cta"
            className="inline-flex items-center gap-1.5 rounded-md border border-[color:var(--mc-accent)] bg-[color:var(--mc-accent-soft)] px-3 py-1.5 text-xs font-semibold text-[color:var(--mc-accent)] hover:bg-[color:var(--mc-accent)] hover:text-[color:var(--mc-text-inverse)]"
          >
            <PlayCircle aria-hidden className="h-3.5 w-3.5" />
            See the 3D demo
          </Link>
        }
      >
        <ul className="space-y-1.5 text-sm text-base-700">
          <li>• Approved missions are replayable from committed artifacts.</li>
          <li>• Rejected missions show the exact validator or supervisor reason.</li>
          <li>• Each row is byte-identical between runs; nothing is synthesised at render time.</li>
        </ul>
      </Panel>

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
