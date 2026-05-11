import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { MissionStoryPanel } from "@/components/MissionStoryPanel";
import type { RehearsalAudit } from "@/adapters/types";

const ACCEPTED_AUDIT: RehearsalAudit = {
  request: {
    request_id: "r",
    description: "Drive to dock",
    mission_id: "m",
    proposal_source: "Drive forward then dock.",
    requested_at_utc: "2026-05-11T00:00:00+00:00",
    seed: 42,
    operator: "alice",
    odd_profile_id: "default",
    notes: [],
  },
  plan: null,
  validation_diagnostics: [],
  decision: {
    decision_id: "d1",
    decision_status: "approved",
    safety_status: "safe",
    rationale: ["accepted"],
    rejected_reasons: [],
    allowed_topics: ["/cmd_vel_requested"],
    forbidden_topics: ["/cmd_vel"],
    requires_human_review: false,
    decided_at_utc: "2026-05-11T00:00:01+00:00",
  },
  runtime: {
    mission_id: "m",
    final_status: "completed",
    final_failure_reason: "",
    safety_status: "safe",
    events: [],
    deterministic_hash: "hash",
    started_at_utc: "2026-05-11T00:00:02+00:00",
    finished_at_utc: "2026-05-11T00:00:03+00:00",
    timeline: { transitions: [], rendered_markdown: "", rendered_mermaid: "" },
  },
  replay: null,
  analytics: null,
  final_status: "completed",
  final_failure_reason: "",
  safety_status: "safe",
  generated_at_utc: "",
  disclaimer: "",
  mission_rehearsal_version: "phase16-1",
};

describe("MissionStoryPanel", () => {
  it("renders one step per lifecycle phase for an accepted mission", () => {
    render(<MissionStoryPanel audit={ACCEPTED_AUDIT} />);
    const panel = screen.getByTestId("mission-story-panel");
    expect(panel).toBeInTheDocument();
    const steps = screen.getAllByTestId(/story-step-/);
    expect(steps.length).toBeGreaterThanOrEqual(4);
    expect(screen.getByText(/Validator accepted the plan/i)).toBeInTheDocument();
    expect(screen.getByText(/Supervisor approved the plan/i)).toBeInTheDocument();
    expect(screen.getByText(/Mission completed deterministically/i)).toBeInTheDocument();
  });

  it("marks rejected missions as fail and names the failure reason", () => {
    const rejected: RehearsalAudit = {
      ...ACCEPTED_AUDIT,
      validation_diagnostics: [
        { code: "unsafe_speed", severity: "rejection", message: "too fast" },
      ],
      decision: {
        ...ACCEPTED_AUDIT.decision,
        decision_status: "rejected",
        safety_status: "unsafe_rejected",
        rejected_reasons: ["unsafe_speed"],
        rationale: ["supervisor rejected"],
      },
      runtime: null,
      final_status: "rejected",
      final_failure_reason: "unsafe_speed",
      safety_status: "unsafe_rejected",
    };
    render(<MissionStoryPanel audit={rejected} />);
    expect(screen.getByText(/Validator rejected the plan/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/Supervisor rejected the plan/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Rehearsal not executed/i)).toBeInTheDocument();
    expect(screen.getByText(/Mission rejected: unsafe_speed/i)).toBeInTheDocument();
  });
});
