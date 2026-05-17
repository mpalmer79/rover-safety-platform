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
  const counts = sorted.reduce(
    (acc, a) => {
      const s = String(a.final_status);
      if (s === "completed") acc.completed += 1;
      else if (s === "rejected") acc.rejected += 1;
      else acc.other += 1;
      return acc;
    },
    { completed: 0, rejected: 0, other: 0 },
  );

  return (
    <PageSurface>
      <div className="space-y-6">
        <header
          data-testid="replay-index-hero"
          className="surface-hero relative overflow-hidden px-6 py-7 sm:px-8"
        >
          <span
            aria-hidden
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "radial-gradient(circle at 12% 18%, color-mix(in srgb, var(--mc-accent) 28%, transparent) 0%, transparent 55%), radial-gradient(circle at 88% 92%, color-mix(in srgb, var(--mc-status-aborted) 22%, transparent) 0%, transparent 60%)",
            }}
          />
          <span
            aria-hidden
            className="pointer-events-none absolute inset-x-0 top-0 h-px"
            style={{
              background:
                "linear-gradient(90deg, transparent, color-mix(in srgb, var(--mc-accent) 70%, transparent), transparent)",
            }}
          />
          <div className="relative space-y-3">
            <p className="label">Replay viewer</p>
            <h1 className="display-1">Rehearsal replay index</h1>
            <p className="max-w-2xl text-base-700">
              The replay viewer reconstructs simulated mission outcomes
              from deterministic event artifacts. Pick a row to inspect a
              mission&apos;s event stream, supervisor decision, replay
              markers, and analytics.
            </p>
            <dl className="flex flex-wrap items-center gap-2 pt-1 font-mono text-[11px] uppercase tracking-widest">
              <StatChip
                label="bundles"
                value={sorted.length}
                tone="var(--mc-accent)"
              />
              <StatChip
                label="completed"
                value={counts.completed}
                tone="var(--mc-status-completed)"
              />
              <StatChip
                label="rejected"
                value={counts.rejected}
                tone="var(--mc-status-rejected)"
              />
              {counts.other > 0 ? (
                <StatChip
                  label="other"
                  value={counts.other}
                  tone="var(--mc-status-pending)"
                />
              ) : null}
            </dl>
          </div>
        </header>

        <Panel
          eyebrow="What this proves"
          title="Reviewer summary"
          trailing={
            <Link
              href="/demo/warehouse-replay"
              data-testid="replay-index-demo-cta"
              className="inline-flex items-center gap-1.5 rounded-md border border-[color:var(--mc-accent)] bg-[color:var(--mc-accent-soft)] px-3 py-1.5 text-xs font-semibold text-[color:var(--mc-accent)] transition-colors hover:bg-[color:var(--mc-accent)] hover:text-[color:var(--mc-text-inverse)]"
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

function StatChip({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div
      className="inline-flex items-center gap-2 rounded-full border px-2.5 py-1"
      style={{
        borderColor: `color-mix(in srgb, ${tone} 40%, transparent)`,
        background: `color-mix(in srgb, ${tone} 12%, transparent)`,
      }}
    >
      <span
        aria-hidden
        className="inline-block h-1.5 w-1.5 rounded-full"
        style={{ background: tone }}
      />
      <span style={{ color: tone }}>{value}</span>
      <span className="text-base-600">{label}</span>
    </div>
  );
}
