import {
  coerceSpatialReplayArtifact,
  type SpatialReplayRaw,
} from "@/adapters/loader";
import type { RehearsalAudit } from "@/adapters/types";
import { PageSurface } from "@/components/PageSurface";

import auditJson from "./data/rehearsal-audit.json";
import spatialJson from "./data/spatial-replay.json";
import { DEMO_MISSION } from "./sample-demo-mission";
import { WarehouseReplayDemo } from "./WarehouseReplayDemo";

export const dynamic = "force-static";

export const metadata = {
  title: "Warehouse Mission Replay · ProjectBoundary",
  description:
    "Polished 3D replay of an approved warehouse mission, driven by deterministic spatial replay artifacts.",
};

// The demo route bundles its canonical artifacts at build time so the
// prerender never touches the filesystem. This sidesteps any Vercel
// "Root Directory" / sparse-checkout interaction that previously
// surfaced as the route error boundary in production.
const audit = auditJson as unknown as RehearsalAudit;
const spatialReplay = coerceSpatialReplayArtifact(
  spatialJson as unknown as SpatialReplayRaw,
);

export default function WarehouseReplayDemoPage() {
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
