import Link from "next/link";

import {
  loadRehearsalAudit,
  loadSpatialReplay,
} from "@/adapters/loader";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";
import { GradientPanel } from "@/components/GradientPanel";

import { DEMO_MISSION } from "./sample-demo-mission";
import { WarehouseReplayDemo } from "./WarehouseReplayDemo";

export const dynamic = "force-static";

export const metadata = {
  title: "Warehouse Mission Replay · ProjectBoundary",
  description:
    "Polished 3D replay of an approved warehouse mission, driven by deterministic spatial replay artifacts.",
};

type LoadOutcome<T> =
  | { kind: "ok"; value: T }
  | { kind: "missing" }
  | { kind: "error" };

// A non-ENOENT failure (permissions, JSON.parse, EISDIR, missing
// repo files outside Vercel's Root Directory) must not surface as
// a route error boundary on this reviewer-facing page. Degrade to
// the existing 2D narrative shell and tell the reviewer what
// happened. The fallback distinguishes "artifact missing" from
// "loader raised an unexpected error" so honesty is preserved.
async function safeLoad<T>(
  label: string,
  load: () => Promise<T | null>,
): Promise<LoadOutcome<T>> {
  try {
    const value = await load();
    return value === null ? { kind: "missing" } : { kind: "ok", value };
  } catch (err) {
    const e = err as NodeJS.ErrnoException;
    // Server-side log so Vercel build logs capture the real cause.
    // The reviewer page never surfaces this directly.
    // eslint-disable-next-line no-console
    console.warn(
      "[demo/warehouse-replay] " +
        label +
        " loader raised non-ENOENT error: " +
        JSON.stringify({
          name: e?.name ?? "Error",
          code: e?.code,
          message: e?.message ?? String(err),
          path: e?.path,
          cwd: typeof process !== "undefined" ? process.cwd() : undefined,
        }),
    );
    return { kind: "error" };
  }
}

export default async function WarehouseReplayDemoPage() {
  const [auditOutcome, spatialOutcome] = await Promise.all([
    safeLoad("rehearsal-audit", () =>
      loadRehearsalAudit(DEMO_MISSION.rehearsalId),
    ),
    safeLoad("spatial-replay", () =>
      loadSpatialReplay(DEMO_MISSION.spatialRunId),
    ),
  ]);

  if (auditOutcome.kind !== "ok" || spatialOutcome.kind !== "ok") {
    return (
      <FallbackPage
        auditOutcome={auditOutcome.kind}
        spatialOutcome={spatialOutcome.kind}
      />
    );
  }

  const audit = auditOutcome.value;
  const spatialReplay = spatialOutcome.value;
  const evidenceLinks = [
    {
      label: `Open mission audit · ${DEMO_MISSION.rehearsalId}`,
      href: `/missions/${DEMO_MISSION.rehearsalId}`,
    },
    { label: "Inspect Safety Authority chain", href: "/safety" },
    { label: "Open Reviewer Walkthrough", href: "/walkthrough" },
    { label: "Open Evidence & Audit explorer", href: "/evidence" },
  ];

  return (
    <PageSurface variant="hero">
      <WarehouseReplayDemo
        descriptor={DEMO_MISSION}
        plan={audit.plan}
        events={audit.runtime?.events ?? []}
        spatialReplay={spatialReplay}
        evidenceLinks={evidenceLinks}
      />
      <p className="mt-6 text-xs text-[color:var(--mc-text-muted)]">
        Mission Replay Demo. This scene reconstructs a simulated rover
        mission from deterministic replay artifacts. The rover only
        moves after validation and safety-supervisor approval. The
        visualization is simulation-only and does not control real
        hardware.
      </p>
    </PageSurface>
  );
}

type OutcomeKind = "ok" | "missing" | "error";

function describeReason(audit: OutcomeKind, spatial: OutcomeKind): string {
  const auditError = audit === "error";
  const spatialError = spatial === "error";
  if (auditError && spatialError) {
    return "the rehearsal-audit and spatial-replay adapters both raised an unexpected (non-ENOENT) error while reading committed JSON";
  }
  if (auditError) {
    return "the rehearsal-audit adapter raised an unexpected (non-ENOENT) error while reading committed JSON";
  }
  if (spatialError) {
    return "the spatial-replay adapter raised an unexpected (non-ENOENT) error while reading committed JSON";
  }
  if (audit === "missing" && spatial === "missing") {
    return "no rehearsal audit or spatial scene artifact is registered in the public export";
  }
  if (spatial === "missing") {
    return "no spatial scene artifact is registered for this run";
  }
  return "no rehearsal audit is registered for this mission";
}

function FallbackPage({
  auditOutcome,
  spatialOutcome,
}: {
  auditOutcome: OutcomeKind;
  spatialOutcome: OutcomeKind;
}) {
  const reason = describeReason(auditOutcome, spatialOutcome);
  return (
    <PageSurface>
      <div className="space-y-5">
        <GradientPanel elevated className="px-5 py-5">
          <p className="label">Mission Replay Demo</p>
          <h1 className="display-1">2D fallback active</h1>
          <p
            data-testid="demo-fallback-reason"
            className="text-base text-[color:var(--mc-text)]"
          >
            3D replay is available for the canonical demo mission. This
            mission currently uses 2D fallback mode because {reason}.
            The static export and safety-supervisor authority are
            unaffected.
          </p>
        </GradientPanel>
        <Panel eyebrow="Reviewer paths" title="What to do next">
          <ul className="space-y-2 text-sm">
            <li>
              •{" "}
              <Link
                href="/replay"
                className="text-[color:var(--mc-accent)] underline-offset-2 hover:underline"
              >
                Open the rehearsal replay index
              </Link>{" "}
              to pick another mission.
            </li>
            <li>
              •{" "}
              <Link
                href="/safety"
                className="text-[color:var(--mc-accent)] underline-offset-2 hover:underline"
              >
                Inspect the Safety Authority chain
              </Link>
              .
            </li>
            <li>
              •{" "}
              <Link
                href="/start"
                className="text-[color:var(--mc-accent)] underline-offset-2 hover:underline"
              >
                Return to Start Here
              </Link>{" "}
              for the recommended reviewer flow.
            </li>
          </ul>
        </Panel>
      </div>
    </PageSurface>
  );
}
