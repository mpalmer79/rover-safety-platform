/**
 * Phase 20 reviewer walkthrough tests.
 *
 * Asserts:
 *   * the walkthrough exposes exactly ten deterministic steps;
 *   * the overlay progresses forward and back without losing state;
 *   * each step renders its narrative + evidence + safety + outcome
 *     verbatim from steps.ts.
 */

import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { ThemeProvider } from "@/lib/theme-provider";
import { ReviewerWalkthroughOverlay } from "@/reviewer/components/ReviewerWalkthroughOverlay";
import {
  WALKTHROUGH_STEPS,
  WALKTHROUGH_STEP_COUNT,
} from "@/reviewer/steps";
import { WalkthroughProgress } from "@/reviewer/components/WalkthroughProgress";
import { WalkthroughStepCard } from "@/reviewer/components/WalkthroughStepCard";
import { WalkthroughNarrativePanel } from "@/reviewer/components/WalkthroughNarrativePanel";
import { WalkthroughEvidencePanel } from "@/reviewer/components/WalkthroughEvidencePanel";
import { WalkthroughSafetyPanel } from "@/reviewer/components/WalkthroughSafetyPanel";
import { WalkthroughOutcomePanel } from "@/reviewer/components/WalkthroughOutcomePanel";

function wrap(node: React.ReactNode) {
  return <ThemeProvider>{node}</ThemeProvider>;
}

describe("reviewer walkthrough", () => {
  it("exposes exactly 10 steps", () => {
    expect(WALKTHROUGH_STEP_COUNT).toBe(10);
    expect(WALKTHROUGH_STEPS).toHaveLength(10);
  });

  it("step indices are 1-based and sequential", () => {
    WALKTHROUGH_STEPS.forEach((step, idx) => {
      expect(step.index).toBe(idx + 1);
    });
  });

  it("renders the first step on mount", () => {
    render(wrap(<ReviewerWalkthroughOverlay />));
    expect(screen.getByText("Operator request")).toBeInTheDocument();
    expect(screen.getByText(/1 \/ 10/)).toBeInTheDocument();
  });

  it("advances to the next step on click", () => {
    render(wrap(<ReviewerWalkthroughOverlay />));
    fireEvent.click(screen.getByTestId("walkthrough-next"));
    expect(screen.getByText("Proposal generation")).toBeInTheDocument();
    expect(screen.getByText(/2 \/ 10/)).toBeInTheDocument();
  });

  it("disables back at step 1", () => {
    render(wrap(<ReviewerWalkthroughOverlay />));
    const back = screen.getByTestId("walkthrough-previous") as HTMLButtonElement;
    expect(back.disabled).toBe(true);
  });

  it("disables next at step 10", () => {
    render(wrap(<ReviewerWalkthroughOverlay startIndex={9} />));
    const next = screen.getByTestId("walkthrough-next") as HTMLButtonElement;
    expect(next.disabled).toBe(true);
  });

  it("reset returns to step 1", () => {
    render(wrap(<ReviewerWalkthroughOverlay startIndex={5} />));
    expect(screen.getByText(/6 \/ 10/)).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("walkthrough-reset"));
    expect(screen.getByText(/1 \/ 10/)).toBeInTheDocument();
  });

  it("WalkthroughProgress renders 10 segments with the correct fill count", () => {
    render(<WalkthroughProgress current={3} />);
    const filled = screen
      .getByTestId("walkthrough-progress")
      .querySelectorAll('[data-filled="true"]');
    expect(filled.length).toBe(3);
  });

  it("each subpanel renders the supplied step verbatim", () => {
    const step = WALKTHROUGH_STEPS[0];
    render(
      <ThemeProvider>
        <WalkthroughStepCard step={step} />
        <WalkthroughNarrativePanel step={step} />
        <WalkthroughEvidencePanel step={step} />
        <WalkthroughSafetyPanel step={step} />
        <WalkthroughOutcomePanel step={step} />
      </ThemeProvider>,
    );
    expect(screen.getAllByText(step.title).length).toBeGreaterThan(0);
    expect(screen.getAllByText(step.outcome).length).toBeGreaterThan(0);
    expect(screen.getAllByText(step.safety).length).toBeGreaterThan(0);
    expect(screen.getByText(step.evidence[0])).toBeInTheDocument();
  });

  it("the walkthrough renders the simulation-only banner copy", () => {
    render(wrap(<ReviewerWalkthroughOverlay />));
    expect(screen.getByText(/Simulation-only/)).toBeInTheDocument();
  });
});
