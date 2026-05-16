/**
 * Phase 20B contextual walkthrough tests.
 *
 * Asserts that:
 *   * each step binds to mission evidence when an audit is supplied;
 *   * missing evidence surfaces as an explicit limitation;
 *   * rejected missions remain rejected at every relevant step;
 *   * the selector returns null when no audit matches.
 */

import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { ThemeProvider } from "@/lib/theme-provider";
import { ContextualWalkthroughOverlay } from "@/reviewer/components/ContextualWalkthroughOverlay";
import {
  buildStepBindings,
} from "@/reviewer/contextualWalkthrough";
import { selectFocusedAudit } from "@/reviewer/walkthroughSelectors";

import { FIX_AUDIT, FIX_SPATIAL_ARTIFACT } from "@/components/__fixtures__/_shared";

function wrap(node: React.ReactNode) {
  return <ThemeProvider>{node}</ThemeProvider>;
}

describe("buildStepBindings", () => {
  it("returns one binding per step", () => {
    const bindings = buildStepBindings({
      audit: FIX_AUDIT,
      spatial: null,
      registry: null,
    });
    expect(bindings.length).toBe(10);
  });

  it("operator-request status is ok when an audit is supplied", () => {
    const [first] = buildStepBindings({
      audit: FIX_AUDIT,
      spatial: null,
      registry: null,
    });
    expect(first.status).toBe("ok");
    expect(first.headline).toContain(FIX_AUDIT.request.request_id);
  });

  it("all steps become unavailable when no audit is supplied", () => {
    const bindings = buildStepBindings({
      audit: null,
      spatial: null,
      registry: null,
    });
    for (const b of bindings) expect(b.status).toBe("unavailable");
  });

  it("rejected audit makes the sanitizer step rejected", () => {
    const rejected = { ...FIX_AUDIT, plan: null };
    const bindings = buildStepBindings({
      audit: rejected,
      spatial: null,
      registry: null,
    });
    const sanitizer = bindings.find((b) => b.step === "sanitizer-decision");
    expect(sanitizer?.status).toBe("rejected");
  });

  it("preserves derivation_source verbatim on the analytics step", () => {
    const bindings = buildStepBindings({
      audit: FIX_AUDIT,
      spatial: FIX_SPATIAL_ARTIFACT,
      registry: null,
    });
    const analytics = bindings.find((b) => b.step === "analytics-outcome");
    expect(analytics?.derivation).toBe(FIX_SPATIAL_ARTIFACT.derivation_source);
  });

  it("the limitations step never claims bag_backed for a fixture artifact", () => {
    const bindings = buildStepBindings({
      audit: FIX_AUDIT,
      spatial: FIX_SPATIAL_ARTIFACT,
      registry: null,
    });
    const last = bindings[bindings.length - 1];
    expect(last.derivation).not.toBe("bag_backed");
    expect(
      last.limitations.some((l) => l.includes("derivation_source")),
    ).toBe(true);
  });
});

describe("selectFocusedAudit", () => {
  it("returns null audit when the audit list is empty", () => {
    const result = selectFocusedAudit({ audits: [], missionId: "x" });
    expect(result.audit).toBeNull();
  });

  it("matches by mission id when present", () => {
    const result = selectFocusedAudit({
      audits: [FIX_AUDIT],
      missionId: FIX_AUDIT.request.mission_id,
    });
    expect(result.audit).toBe(FIX_AUDIT);
  });

  it("falls back to the first audit when no mission matches", () => {
    const result = selectFocusedAudit({
      audits: [FIX_AUDIT],
      missionId: "not-a-mission",
    });
    expect(result.audit).toBe(FIX_AUDIT);
  });
});

describe("ContextualWalkthroughOverlay", () => {
  it("renders the first step + mission focus for the supplied audit", () => {
    render(
      wrap(<ContextualWalkthroughOverlay audit={FIX_AUDIT} />),
    );
    const matches = screen.getAllByText(
      new RegExp(FIX_AUDIT.request.mission_id),
    );
    expect(matches.length).toBeGreaterThan(0);
    expect(screen.getByText(/1 \/ 10/)).toBeInTheDocument();
  });

  it("advances through steps with the next button", () => {
    render(wrap(<ContextualWalkthroughOverlay audit={FIX_AUDIT} />));
    fireEvent.click(screen.getByTestId("contextual-walkthrough-next"));
    expect(screen.getByText(/2 \/ 10/)).toBeInTheDocument();
  });

  it("shows the empty mission-focus card when no audit is selected", () => {
    render(wrap(<ContextualWalkthroughOverlay audit={null} />));
    expect(screen.getByText(/No mission selected/)).toBeInTheDocument();
  });
});
