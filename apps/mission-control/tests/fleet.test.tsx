/**
 * Phase 20 fleet / site review tests.
 *
 * Asserts:
 *   * site fixture is deterministic;
 *   * readiness derivation never recodes the input;
 *   * fleet panels render the disclaimer verbatim and never
 *     fabricate runtime state.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { ThemeProvider } from "@/lib/theme-provider";
import {
  CANONICAL_SITE,
  REFERENCE_ZONE_STATUS,
  buildMissionQueue,
  deriveRobotReadiness,
} from "@/site";
import {
  FleetOverviewPanel,
  MissionQueuePanel,
  RobotReadinessCard,
  SiteMapOverview,
  ZoneStatusPanel,
} from "@/site/components";

function wrap(node: React.ReactNode) {
  return <ThemeProvider>{node}</ThemeProvider>;
}

describe("canonical site", () => {
  it("ships one robot, three zones", () => {
    expect(CANONICAL_SITE.robots).toHaveLength(1);
    expect(CANONICAL_SITE.zones).toHaveLength(3);
  });

  it("carries a verbatim simulation-only disclaimer", () => {
    expect(CANONICAL_SITE.disclaimer).toMatch(/Simulation-only/);
    expect(CANONICAL_SITE.disclaimer).toMatch(/not safety-certified/);
  });
});

describe("readiness derivation", () => {
  it("returns evidence_missing when no audit exists", () => {
    const r = deriveRobotReadiness({
      robotId: "rover-001",
      hasAudit: false,
      finalStatus: null,
      lastRehearsalId: null,
      openIssues: [],
    });
    expect(r.state).toBe("evidence_missing");
  });

  it("returns blocked when the last status is rejected", () => {
    const r = deriveRobotReadiness({
      robotId: "rover-001",
      hasAudit: true,
      finalStatus: "rejected",
      lastRehearsalId: "x",
      openIssues: [],
    });
    expect(r.state).toBe("blocked");
  });

  it("returns ready_to_rehearse when the last status is completed", () => {
    const r = deriveRobotReadiness({
      robotId: "rover-001",
      hasAudit: true,
      finalStatus: "completed",
      lastRehearsalId: "x",
      openIssues: [],
    });
    expect(r.state).toBe("ready_to_rehearse");
  });

  it("returns needs_review for any other status", () => {
    const r = deriveRobotReadiness({
      robotId: "rover-001",
      hasAudit: true,
      finalStatus: "paused",
      lastRehearsalId: "x",
      openIssues: [],
    });
    expect(r.state).toBe("needs_review");
  });
});

describe("mission queue", () => {
  it("preserves the entries verbatim", () => {
    const queue = buildMissionQueue({
      siteId: CANONICAL_SITE.site_id,
      generatedAtUtc: "2026-05-12T00:00:00Z",
      entries: [
        {
          missionId: "m1",
          description: "desc",
          auditRequestId: "r1",
          readinessState: "ready_to_rehearse",
          readinessReason: "ok",
        },
      ],
    });
    expect(queue.entries[0].mission_id).toBe("m1");
    expect(queue.entries[0].readiness).toBe("ready_to_rehearse");
  });
});

describe("fleet panels", () => {
  it("FleetOverviewPanel renders the site disclaimer", () => {
    render(
      wrap(
        <FleetOverviewPanel
          site={CANONICAL_SITE}
          readyCount={1}
          blockedCount={0}
        />,
      ),
    );
    expect(screen.getByText(/Simulation-only/)).toBeInTheDocument();
    expect(screen.getByText(/ready · 1/)).toBeInTheDocument();
  });

  it("SiteMapOverview renders every zone label", () => {
    render(wrap(<SiteMapOverview site={CANONICAL_SITE} />));
    for (const zone of CANONICAL_SITE.zones) {
      expect(screen.getByText(zone.label)).toBeInTheDocument();
    }
  });

  it("MissionQueuePanel reports 'no queued missions' on empty input", () => {
    render(
      wrap(
        <MissionQueuePanel
          queue={{
            site_id: CANONICAL_SITE.site_id,
            generated_at_utc: "",
            entries: [],
          }}
        />,
      ),
    );
    expect(screen.getByText(/No queued missions/i)).toBeInTheDocument();
  });

  it("RobotReadinessCard renders the readiness reason verbatim", () => {
    const robot = CANONICAL_SITE.robots[0];
    const readiness = deriveRobotReadiness({
      robotId: robot.robot_id,
      hasAudit: false,
      finalStatus: null,
      lastRehearsalId: null,
      openIssues: [],
    });
    render(wrap(<RobotReadinessCard profile={robot} readiness={readiness} />));
    expect(screen.getByText(/No rehearsal audit on disk/)).toBeInTheDocument();
  });

  it("ZoneStatusPanel renders forbidden topics verbatim", () => {
    render(wrap(<ZoneStatusPanel statuses={REFERENCE_ZONE_STATUS} />));
    expect(screen.getAllByText(/\/cmd_vel/).length).toBeGreaterThan(0);
  });
});
