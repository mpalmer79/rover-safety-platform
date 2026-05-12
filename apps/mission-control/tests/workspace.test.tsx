/**
 * Phase 20 operator workspace tests.
 *
 * These tests pin:
 *   * preset shape is deterministic (no drag/drop persistence),
 *   * every preset id resolves to a complete preset,
 *   * the shell + topbar + status strip render without runtime
 *     errors and never claim live telemetry.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

import { ThemeProvider } from "@/lib/theme-provider";
import {
  WORKSPACE_PRESETS,
  WORKSPACE_PRESET_IDS,
  isWorkspacePresetId,
  workspacePreset,
} from "@/workspaces/presets";
import { WorkspaceTopbar } from "@/workspaces/components/WorkspaceTopbar";
import { WorkspaceSidebar } from "@/workspaces/components/WorkspaceSidebar";
import { WorkspaceStatusStrip } from "@/workspaces/components/WorkspaceStatusStrip";
import { WorkspacePresetSwitcher } from "@/workspaces/components/WorkspacePresetSwitcher";
import { WorkspacePanelGrid } from "@/workspaces/components/WorkspacePanelGrid";
import { WorkspaceBreadcrumbs } from "@/workspaces/components/WorkspaceBreadcrumbs";

describe("workspace presets", () => {
  it("exports six deterministic presets", () => {
    expect(WORKSPACE_PRESET_IDS).toEqual([
      "mission-review",
      "safety-review",
      "replay-analysis",
      "evidence-audit",
      "fleet-readiness",
      "reviewer-walkthrough",
    ]);
  });

  it("each preset has a complete shape", () => {
    for (const id of WORKSPACE_PRESET_IDS) {
      const preset = workspacePreset(id);
      expect(preset.id).toBe(id);
      expect(preset.title.length).toBeGreaterThan(0);
      expect(preset.subtitle.length).toBeGreaterThan(0);
      expect(preset.panels.length).toBeGreaterThan(0);
      expect(preset.audience.length).toBeGreaterThan(0);
    }
  });

  it("rejects unknown preset ids", () => {
    expect(isWorkspacePresetId("not-a-real-preset")).toBe(false);
    expect(isWorkspacePresetId("mission-review")).toBe(true);
  });

  it("panel layouts use deterministic col/row spans", () => {
    for (const preset of Object.values(WORKSPACE_PRESETS)) {
      for (const layout of preset.panels) {
        expect(layout.colSpan).toBeGreaterThan(0);
        expect(layout.colSpan).toBeLessThanOrEqual(12);
        expect(layout.rowSpan).toBeGreaterThan(0);
        expect(layout.rowSpan).toBeLessThanOrEqual(6);
      }
    }
  });
});

describe("workspace topbar", () => {
  it("renders the active preset title + honesty pill", () => {
    render(
      <ThemeProvider>
        <WorkspaceTopbar preset={workspacePreset("mission-review")} />
      </ThemeProvider>,
    );
    expect(screen.getByText("Mission Review")).toBeInTheDocument();
    expect(screen.getByText(/Simulation-only/)).toBeInTheDocument();
  });

  it("never claims live telemetry", () => {
    const { container } = render(
      <ThemeProvider>
        <WorkspaceTopbar preset={workspacePreset("safety-review")} />
      </ThemeProvider>,
    );
    expect(container.textContent).not.toMatch(/live/i);
    expect(container.textContent).not.toMatch(/streaming/i);
  });
});

describe("workspace sidebar", () => {
  it("lists every preset as a link", () => {
    render(
      <ThemeProvider>
        <WorkspaceSidebar active="mission-review" />
      </ThemeProvider>,
    );
    for (const id of WORKSPACE_PRESET_IDS) {
      const preset = workspacePreset(id);
      expect(screen.getAllByText(preset.title).length).toBeGreaterThan(0);
    }
  });
});

describe("workspace status strip", () => {
  it("renders the bag-backed count verbatim", () => {
    render(
      <ThemeProvider>
        <WorkspaceStatusStrip
          rehearsalCount={3}
          bagBackedCount={0}
          requirementCount={42}
          missionId="warehouse_pickup_route_alpha"
          generatedAtUtc="2026-05-12T00:00:00Z"
        />
      </ThemeProvider>,
    );
    expect(screen.getByText(/bag-backed · 0/)).toBeInTheDocument();
    expect(screen.getByText(/3 rehearsal audits/)).toBeInTheDocument();
    expect(screen.getByText(/42 requirements/)).toBeInTheDocument();
  });
});

describe("workspace preset switcher", () => {
  it("emits a deterministic link per preset", () => {
    render(
      <ThemeProvider>
        <WorkspacePresetSwitcher active="mission-review" />
      </ThemeProvider>,
    );
    const list = screen.getByTestId("workspace-preset-switcher");
    const links = list.querySelectorAll("a[href^='/workspaces/']");
    expect(links.length).toBe(WORKSPACE_PRESET_IDS.length);
  });
});

describe("workspace panel grid", () => {
  it("renders a placeholder for unregistered panels", () => {
    render(
      <ThemeProvider>
        <WorkspacePanelGrid
          preset={workspacePreset("mission-review")}
          nodes={{}}
        />
      </ThemeProvider>,
    );
    const grid = screen.getByTestId("workspace-panel-grid");
    expect(grid.getAttribute("data-preset")).toBe("mission-review");
    // Every panel slot should render even without a registered node.
    expect(grid.querySelectorAll("[data-panel-id]").length).toBeGreaterThan(0);
  });
});

describe("workspace breadcrumbs", () => {
  it("marks the last entry aria-current", () => {
    render(
      <WorkspaceBreadcrumbs
        entries={[
          { label: "Mission Control", href: "/" },
          { label: "Workspaces", href: "/workspaces" },
          { label: "Mission Review" },
        ]}
      />,
    );
    expect(screen.getByText("Mission Review").getAttribute("aria-current")).toBe(
      "page",
    );
  });
});
