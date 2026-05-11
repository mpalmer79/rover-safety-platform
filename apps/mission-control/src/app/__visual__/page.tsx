/**
 * Component visual catalog (Item 4, temporary).
 *
 * Renders each component in a card so the Playwright visual
 * regression suite can screenshot per-component DOM. Item 5
 * replaces this with the permanent /catalog route (with
 * src/components/__fixtures__/ files driving the state variants).
 *
 * This route is intentionally NOT linked from the SiteNav today;
 * it exists for screenshot evidence only. The catalog renders
 * inside the standard PageSurface so the prerendered HTML still
 * carries the SafetyBoundaryBanner via the root layout.
 */

import { ArtifactIntegrityBadge } from "@/components/ArtifactIntegrityBadge";
import { EvidenceStatusChip } from "@/components/EvidenceStatusChip";
import { GradientPanel } from "@/components/GradientPanel";
import { MissionEventMarker } from "@/components/MissionEventMarker";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";
import { RequirementBadge } from "@/components/RequirementBadge";
import { RiskBandBadge } from "@/components/RiskBandBadge";
import { SafetyBoundaryBanner } from "@/components/SafetyBoundaryBanner";
import { SpatialReplayBadge } from "@/components/SpatialReplayBadge";
import { StatusPill } from "@/components/StatusPill";
import { ThemeToggle } from "@/components/ThemeToggle";
import { WarehouseLaneMap } from "@/components/WarehouseLaneMap";

export const dynamic = "force-static";

interface CatalogCardProps {
  id: string;
  name: string;
  description: string;
  children: React.ReactNode;
}

function CatalogCard({ id, name, description, children }: CatalogCardProps) {
  return (
    <Panel
      eyebrow="component"
      title={name}
    >
      <div
        data-testid={`catalog-card-${id}`}
        className="space-y-3"
      >
        <p className="text-muted text-sm">{description}</p>
        <div className="rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] p-4">
          {children}
        </div>
      </div>
    </Panel>
  );
}

export default function VisualCatalogPage() {
  return (
    <PageSurface>
      <GradientPanel elevated className="px-4 py-4 sm:px-5 sm:py-5">
        <header className="space-y-1">
          <p className="label">Visual regression catalog</p>
          <h1 className="display-1">Components</h1>
          <p className="text-muted text-sm">
            One card per component. Item 4 uses this as the visual
            regression source; Item 5 replaces it with the permanent
            <code> /catalog</code> route.
          </p>
        </header>
      </GradientPanel>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <CatalogCard
          id="SafetyBoundaryBanner"
          name="SafetyBoundaryBanner"
          description="Top-of-page banner that asserts the simulation-only boundary."
        >
          <SafetyBoundaryBanner />
        </CatalogCard>

        <CatalogCard
          id="ThemeToggle"
          name="ThemeToggle"
          description="Medium-emphasis light/dark toggle."
        >
          <ThemeToggle emphasis="medium" />
        </CatalogCard>

        <CatalogCard
          id="StatusPill-completed"
          name="StatusPill — completed"
          description="Status pill for the completed mission state."
        >
          <StatusPill label="completed" />
        </CatalogCard>

        <CatalogCard
          id="StatusPill-rejected"
          name="StatusPill — rejected"
          description="Status pill for the rejected mission state."
        >
          <StatusPill label="rejected" />
        </CatalogCard>

        <CatalogCard
          id="RiskBandBadge"
          name="RiskBandBadge"
          description="Risk band badge."
        >
          <div className="flex flex-wrap gap-2">
            <RiskBandBadge band="low" />
            <RiskBandBadge band="guarded" />
            <RiskBandBadge band="restricted" />
            <RiskBandBadge band="blocked" />
          </div>
        </CatalogCard>

        <CatalogCard
          id="RequirementBadge"
          name="RequirementBadge"
          description="Requirement badge with status."
        >
          <div className="flex flex-wrap gap-2">
            <RequirementBadge reqId="REQ-SAFE-001" status="passed" />
            <RequirementBadge reqId="REQ-LIVE-001" status="not_executed" />
          </div>
        </CatalogCard>

        <CatalogCard
          id="EvidenceStatusChip"
          name="EvidenceStatusChip"
          description="Evidence chip preserving bag-backed input verbatim."
        >
          <div className="flex flex-wrap gap-2">
            <EvidenceStatusChip status="simulated" bagBacked={false} />
            <EvidenceStatusChip status="static_only" bagBacked={false} />
            <EvidenceStatusChip status="not_evaluated" bagBacked={false} />
          </div>
        </CatalogCard>

        <CatalogCard
          id="SpatialReplayBadge"
          name="SpatialReplayBadge"
          description="Spatial-replay derivation-source badge."
        >
          <div className="flex flex-wrap gap-2">
            <SpatialReplayBadge source="bag_backed" />
            <SpatialReplayBadge source="fixture" />
            <SpatialReplayBadge source="bounded_inputs" />
            <SpatialReplayBadge source="topology_only" />
            <SpatialReplayBadge source="unavailable" />
          </div>
        </CatalogCard>

        <CatalogCard
          id="ArtifactIntegrityBadge"
          name="ArtifactIntegrityBadge"
          description="Artifact integrity badge."
        >
          <div className="flex flex-wrap gap-2">
            <ArtifactIntegrityBadge integrity="passed" />
            <ArtifactIntegrityBadge integrity="partial" />
            <ArtifactIntegrityBadge integrity="failed" />
            <ArtifactIntegrityBadge integrity="missing" />
            <ArtifactIntegrityBadge integrity="unverified" />
          </div>
        </CatalogCard>

        <CatalogCard
          id="MissionEventMarker"
          name="MissionEventMarker"
          description="Event-severity marker."
        >
          <div className="flex flex-wrap gap-3">
            <MissionEventMarker severity="info" label="info" />
            <MissionEventMarker severity="warning" label="warning" />
            <MissionEventMarker severity="rejection" label="rejection" />
          </div>
        </CatalogCard>

        <CatalogCard
          id="WarehouseLaneMap"
          name="WarehouseLaneMap"
          description="Illustrative warehouse-lane background."
        >
          <WarehouseLaneMap />
        </CatalogCard>
      </div>
    </PageSurface>
  );
}
