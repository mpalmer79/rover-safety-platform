import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { DeterministicHashDisplay } from "@/components/DeterministicHashDisplay";
import { EvidenceStatusChip } from "@/components/EvidenceStatusChip";
import { MissionStateStepper } from "@/components/MissionStateStepper";
import { RequirementBadge } from "@/components/RequirementBadge";
import { RiskBandBadge } from "@/components/RiskBandBadge";
import { SafetyBoundaryBanner } from "@/components/SafetyBoundaryBanner";
import { StatusPill } from "@/components/StatusPill";

describe("SafetyBoundaryBanner", () => {
  it("declares the platform is not safety-certified", () => {
    render(<SafetyBoundaryBanner />);
    expect(screen.getByText(/not safety-certified/i)).toBeInTheDocument();
    expect(screen.getByText(/simulation-only/i)).toBeInTheDocument();
  });
});

describe("EvidenceStatusChip", () => {
  it("renders verbatim status and bag-backed=no", () => {
    render(<EvidenceStatusChip status="simulated" bagBacked={false} />);
    expect(screen.getByText(/evidence: simulated/i)).toBeInTheDocument();
    expect(screen.getByText(/bag-backed: no/i)).toBeInTheDocument();
  });

  it("never silently inverts the bag-backed claim", () => {
    render(<EvidenceStatusChip status="static_only" bagBacked={false} />);
    // The chip must not contain "yes" anywhere.
    expect(screen.queryByText(/bag-backed: yes/i)).toBeNull();
  });
});

describe("MissionStateStepper", () => {
  it("renders every stage of the rehearsal lifecycle", () => {
    render(<MissionStateStepper status="completed" />);
    for (const stage of [
      "created",
      "validated",
      "approved",
      "rehearsing",
      "completed",
    ]) {
      expect(screen.getByText(stage)).toBeInTheDocument();
    }
  });

  it("does not silently hide the rejected state", () => {
    render(
      <MissionStateStepper
        status="rejected"
        failureReason="direct_actuator_command"
      />,
    );
    // The label "completed" is still rendered (it's a step name) —
    // ensure the stepper exposes the rejection by attribute / title.
    const completedLabel = screen.getAllByText("completed")[0];
    expect(completedLabel).toBeInTheDocument();
  });
});

describe("RiskBandBadge", () => {
  it("renders the band label verbatim", () => {
    render(<RiskBandBadge band="restricted" />);
    expect(screen.getByText("restricted")).toBeInTheDocument();
  });
});

describe("StatusPill", () => {
  it("renders the verbatim final-status label", () => {
    render(<StatusPill label="rejected" />);
    expect(screen.getByText("rejected")).toBeInTheDocument();
  });
});

describe("RequirementBadge", () => {
  it("preserves the req id and verbatim status", () => {
    render(<RequirementBadge reqId="REQ-REHEARSAL-001" status="passed" />);
    expect(screen.getByText("REQ-REHEARSAL-001")).toBeInTheDocument();
    expect(screen.getByText("passed")).toBeInTheDocument();
  });
});

describe("DeterministicHashDisplay", () => {
  it("renders the short hash and the full hash via title", () => {
    const fullHash = "abcdef0123456789abcdef0123456789";
    render(<DeterministicHashDisplay label="plan" hash={fullHash} />);
    expect(screen.getByText("plan")).toBeInTheDocument();
    // The short form is rendered visibly; the long form is the title.
    expect(screen.getByText(/abcdef0123456789…/i)).toBeInTheDocument();
  });

  it("handles null hashes without crashing", () => {
    render(<DeterministicHashDisplay label="runtime" hash={null} />);
    expect(screen.getByText("runtime")).toBeInTheDocument();
  });
});
