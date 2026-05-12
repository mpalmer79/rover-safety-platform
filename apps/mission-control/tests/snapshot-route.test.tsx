/**
 * Phase 20B snapshot route + components tests.
 *
 * Asserts the snapshot panel + import card render without network
 * and faithfully present the canonical fixtures.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  usePathname: () => "/workspaces/snapshot",
}));

import { ThemeProvider } from "@/lib/theme-provider";
import {
  CANONICAL_SNAPSHOT_FIXTURES,
  serializeWorkspaceSnapshot,
  snapshotToJsonString,
} from "@/workspaces/snapshot";
import {
  SnapshotIntegrityBadge,
  WorkspaceSnapshotExportButton,
  WorkspaceSnapshotImportCard,
  WorkspaceSnapshotPanel,
  WorkspaceSnapshotSummary,
} from "@/workspaces/snapshot/components";

function wrap(node: React.ReactNode) {
  return <ThemeProvider>{node}</ThemeProvider>;
}

describe("SnapshotIntegrityBadge", () => {
  it("renders the supplied hash", () => {
    render(<SnapshotIntegrityBadge ok hash="ws-abc12345" />);
    expect(screen.getByText("ws-abc12345")).toBeInTheDocument();
  });
});

describe("WorkspaceSnapshotSummary", () => {
  it("renders the canonical mission-review fixture", () => {
    const fixture = CANONICAL_SNAPSHOT_FIXTURES["mission-review"];
    render(wrap(<WorkspaceSnapshotSummary snapshot={fixture} />));
    expect(screen.getByText(fixture.presetId)).toBeInTheDocument();
    expect(screen.getByText(/Simulation-only/)).toBeInTheDocument();
  });
});

describe("WorkspaceSnapshotPanel", () => {
  it("renders the JSON for the supplied snapshot", () => {
    const fixture = CANONICAL_SNAPSHOT_FIXTURES["mission-review"];
    render(wrap(<WorkspaceSnapshotPanel snapshot={fixture} />));
    const pre = screen.getByTestId("workspace-snapshot-json");
    expect(pre.textContent).toContain(fixture.snapshotHash);
  });
});

describe("WorkspaceSnapshotExportButton", () => {
  it("toggles state when clicked", async () => {
    const fixture = CANONICAL_SNAPSHOT_FIXTURES["mission-review"];
    render(wrap(<WorkspaceSnapshotExportButton snapshot={fixture} />));
    const btn = screen.getByTestId("workspace-snapshot-export");
    expect(btn.getAttribute("data-copied")).toBe("false");
    fireEvent.click(btn);
    await waitFor(() =>
      expect(btn.getAttribute("data-copied")).toBe("true"),
    );
  });
});

describe("WorkspaceSnapshotImportCard", () => {
  it("validates a valid pasted JSON", () => {
    const snapshot = serializeWorkspaceSnapshot({
      presetId: "mission-review",
      missionId: "x",
      replayRunId: null,
      selectedEventId: null,
      selectedPanelIds: [],
      walkthroughStep: null,
      cameraMode: "follow",
      evidenceFocus: { kind: "none", ref: null },
      theme: "dark",
      density: "standard",
      capturedAtUtc: null,
    });
    render(
      wrap(
        <WorkspaceSnapshotImportCard
          initialJson={snapshotToJsonString(snapshot)}
        />,
      ),
    );
    expect(screen.getByText(snapshot.snapshotHash)).toBeInTheDocument();
  });

  it("renders an issue list for malformed JSON", () => {
    render(wrap(<WorkspaceSnapshotImportCard initialJson="{ not valid" />));
    expect(screen.getByTestId("workspace-snapshot-import-issues")).toBeInTheDocument();
  });
});
