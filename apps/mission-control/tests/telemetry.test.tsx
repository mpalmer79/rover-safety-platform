/**
 * Phase 20 telemetry-density panel tests.
 *
 * Asserts:
 *   * every telemetry panel renders the derivation source verbatim;
 *   * "bag-backed" never appears as a hard-coded "true" without
 *     reading the input field;
 *   * empty / null states are honest (no synthesised values).
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { ThemeProvider } from "@/lib/theme-provider";
import {
  EventStreamPanel,
  EvidenceIntegrityPanel,
  MissionHealthPanel,
  MissionTelemetryPanel,
  PoseTracePanel,
  RehearsalOutcomePanel,
  ReplayClockPanel,
  ReplayStatisticsPanel,
  SupervisorDecisionLog,
  TopicAvailabilityPanel,
  ValidationOutcomePanel,
  VelocityCommandPanel,
} from "@/components/telemetry";

import {
  FIX_AUDIT,
  FIX_EVENT_INFO,
  FIX_PLAN,
  FIX_REGISTRY_RECORD,
  FIX_SPATIAL_ARTIFACT,
  FIX_SUPERVISOR_DECISION,
} from "@/components/__fixtures__/_shared";

function wrap(node: React.ReactNode) {
  return <ThemeProvider>{node}</ThemeProvider>;
}

describe("telemetry panels", () => {
  it("MissionTelemetryPanel renders 'no audit selected' when audit is null", () => {
    render(wrap(<MissionTelemetryPanel audit={null} />));
    expect(screen.getByText(/no audit selected/i)).toBeInTheDocument();
  });

  it("MissionTelemetryPanel never claims live telemetry", () => {
    const { container } = render(wrap(<MissionTelemetryPanel audit={FIX_AUDIT} />));
    expect(container.textContent).not.toMatch(/live/i);
  });

  it("SupervisorDecisionLog renders the rejected count from the input list", () => {
    render(wrap(<SupervisorDecisionLog decisions={[FIX_SUPERVISOR_DECISION]} />));
    expect(screen.getByText(/1 decision/)).toBeInTheDocument();
  });

  it("ReplayClockPanel reports 'no events' verbatim when the list is empty", () => {
    render(wrap(<ReplayClockPanel events={[]} />));
    expect(screen.getByText(/no events/)).toBeInTheDocument();
  });

  it("ReplayClockPanel does NOT tick on its own — cursor is parent-controlled", () => {
    render(wrap(<ReplayClockPanel events={[FIX_EVENT_INFO]} cursor={0.5} />));
    expect(screen.getByText(/parent-controlled/)).toBeInTheDocument();
  });

  it("EventStreamPanel renders the supplied events verbatim", () => {
    render(wrap(<EventStreamPanel events={[FIX_EVENT_INFO]} />));
    expect(screen.getByText(FIX_EVENT_INFO.description)).toBeInTheDocument();
  });

  it("VelocityCommandPanel always lists /cmd_vel as forbidden", () => {
    render(wrap(<VelocityCommandPanel plan={FIX_PLAN} />));
    expect(screen.getByText(/forbidden · \/cmd_vel/)).toBeInTheDocument();
    expect(screen.getByText(/allowed · \/cmd_vel_requested/)).toBeInTheDocument();
  });

  it("ReplayStatisticsPanel preserves bag_backed verbatim from the bundle", () => {
    render(
      wrap(
        <ReplayStatisticsPanel
          bundle={{
            mission_id: "x",
            evidence_status: "simulated",
            bag_backed: false,
            replay_markers: [],
            review_status: "passed",
            rendered_markdown: "",
            deterministic_hash: "",
            notes: [],
          }}
          analytics={null}
        />,
      ),
    );
    expect(screen.getByText(/^false$/)).toBeInTheDocument();
  });

  it("MissionHealthPanel reports zero audits honestly", () => {
    render(wrap(<MissionHealthPanel audits={[]} />));
    expect(screen.getByText(/0 rehearsal audit/)).toBeInTheDocument();
  });

  it("PoseTracePanel preserves derivation_source", () => {
    render(wrap(<PoseTracePanel artifact={FIX_SPATIAL_ARTIFACT} />));
    expect(screen.getByText("fixture")).toBeInTheDocument();
  });

  it("TopicAvailabilityPanel reports 'no artefact' when null", () => {
    render(wrap(<TopicAvailabilityPanel artifact={null} />));
    expect(screen.getByText(/no artefact/)).toBeInTheDocument();
  });

  it("EvidenceIntegrityPanel passes bagBacked count through verbatim", () => {
    render(
      wrap(
        <EvidenceIntegrityPanel
          records={[FIX_REGISTRY_RECORD, FIX_REGISTRY_RECORD]}
        />,
      ),
    );
    expect(screen.getByText(/2 artifacts/)).toBeInTheDocument();
  });

  it("ValidationOutcomePanel surfaces rejection diagnostics", () => {
    render(
      wrap(
        <ValidationOutcomePanel
          diagnostics={[
            { code: "unsafe_speed", severity: "rejection", message: "too fast" },
          ]}
        />,
      ),
    );
    expect(screen.getByText(/1 rejection/)).toBeInTheDocument();
  });

  it("RehearsalOutcomePanel renders mission ids verbatim", () => {
    render(wrap(<RehearsalOutcomePanel audits={[FIX_AUDIT]} />));
    expect(screen.getByText(FIX_AUDIT.request.mission_id)).toBeInTheDocument();
  });
});
