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

export default async function WarehouseReplayDemoPage() {
  const [audit, spatialReplay] = await Promise.all([
    loadRehearsalAudit(DEMO_MISSION.rehearsalId),
    loadSpatialReplay(DEMO_MISSION.spatialRunId),
  ]);

  if (!audit || !spatialReplay) {
    return <FallbackPage missingAudit={!audit} missingSpatial={!spatialReplay} />;
  }

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

function FallbackPage({
  missingAudit,
  missingSpatial,
}: {
  missingAudit: boolean;
  missingSpatial: boolean;
}) {
  return (
    <PageSurface>
      <div className="space-y-5">
        <GradientPanel elevated className="px-5 py-5">
          <p className="label">Mission Replay Demo</p>
          <h1 className="display-1">2D fallback active</h1>
          <p className="text-base text-[color:var(--mc-text)]">
            3D replay is available for the canonical demo mission. This
            mission currently uses 2D fallback mode because{" "}
            {missingAudit && missingSpatial
              ? "no rehearsal audit or spatial scene artifact is registered in the public export"
              : missingSpatial
                ? "no spatial scene artifact is registered for this run"
                : "no rehearsal audit is registered for this mission"}
            .
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
                href="/"
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
