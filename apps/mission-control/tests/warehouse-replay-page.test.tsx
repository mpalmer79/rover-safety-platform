/**
 * Warehouse Mission Replay server-page guarantees.
 *
 * The demo route is reviewer-facing. A non-ENOENT failure from the
 * artifact adapter (permissions, JSON.parse, EISDIR, files missing
 * outside Vercel's Root Directory) must NOT escape to the route
 * error boundary as "The mission replay demo could not load".
 * Instead the page must degrade to the existing 2D narrative shell
 * and explain — honestly — why.
 *
 * These tests exercise the page's server-side rendering path
 * directly. The 3D scene under WarehouseReplayDemo is covered by
 * tests/warehouse-replay-demo.test.tsx.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  usePathname: () => "/demo/warehouse-replay",
}));

vi.mock("@/adapters/loader", () => ({
  loadRehearsalAudit: vi.fn(async () => null),
  loadSpatialReplay: vi.fn(async () => null),
}));

import * as loader from "@/adapters/loader";
import WarehouseReplayDemoPage from "@/app/demo/warehouse-replay/page";

describe("/demo/warehouse-replay server page", () => {
  beforeEach(() => {
    vi.mocked(loader.loadRehearsalAudit).mockReset();
    vi.mocked(loader.loadSpatialReplay).mockReset();
  });

  it("renders the 2D fallback when both artifacts are missing (ENOENT)", async () => {
    vi.mocked(loader.loadRehearsalAudit).mockResolvedValue(null);
    vi.mocked(loader.loadSpatialReplay).mockResolvedValue(null);

    const Page = await WarehouseReplayDemoPage();
    render(Page);

    expect(
      screen.getByRole("heading", { level: 1, name: /2D fallback active/i }),
    ).toBeInTheDocument();
    const reason = screen.getByTestId("demo-fallback-reason").textContent ?? "";
    expect(reason).toMatch(
      /no rehearsal audit or spatial scene artifact is registered/i,
    );
  });

  it("renders the 2D fallback when only the spatial artifact is missing", async () => {
    vi.mocked(loader.loadRehearsalAudit).mockResolvedValue(
      // The page only reads `plan` and `runtime?.events`; a minimal
      // shape suffices for the truthiness check that gates fallback.
      { plan: {}, runtime: { events: [] } } as never,
    );
    vi.mocked(loader.loadSpatialReplay).mockResolvedValue(null);

    const Page = await WarehouseReplayDemoPage();
    render(Page);

    expect(
      screen.getByRole("heading", { level: 1, name: /2D fallback active/i }),
    ).toBeInTheDocument();
    const reason = screen.getByTestId("demo-fallback-reason").textContent ?? "";
    expect(reason).toMatch(/no spatial scene artifact is registered/i);
  });

  it("falls back to the 2D shell when the rehearsal-audit adapter throws a non-ENOENT error", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    vi.mocked(loader.loadRehearsalAudit).mockRejectedValue(
      Object.assign(new Error("permission denied"), { code: "EACCES" }),
    );
    vi.mocked(loader.loadSpatialReplay).mockResolvedValue(null);

    try {
      const Page = await WarehouseReplayDemoPage();
      render(Page);

      expect(
        screen.getByRole("heading", { level: 1, name: /2D fallback active/i }),
      ).toBeInTheDocument();
      const reason =
        screen.getByTestId("demo-fallback-reason").textContent ?? "";
      expect(reason).toMatch(
        /rehearsal-audit adapter raised an unexpected \(non-ENOENT\) error/i,
      );

      // The diagnostic warning is logged server-side so Vercel build
      // logs capture the cause. Reviewers never see it on the page.
      expect(warn).toHaveBeenCalled();
      const logged = (warn.mock.calls[0]?.[0] ?? "") as string;
      expect(logged).toMatch(/rehearsal-audit/);
      expect(logged).toMatch(/EACCES/);
    } finally {
      warn.mockRestore();
    }
  });

  it("falls back to the 2D shell when the spatial-replay adapter throws a SyntaxError (malformed JSON)", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    vi.mocked(loader.loadRehearsalAudit).mockResolvedValue(
      { plan: {}, runtime: { events: [] } } as never,
    );
    vi.mocked(loader.loadSpatialReplay).mockRejectedValue(
      new SyntaxError("Unexpected token } in JSON at position 42"),
    );

    try {
      const Page = await WarehouseReplayDemoPage();
      render(Page);

      expect(
        screen.getByRole("heading", { level: 1, name: /2D fallback active/i }),
      ).toBeInTheDocument();
      const reason =
        screen.getByTestId("demo-fallback-reason").textContent ?? "";
      expect(reason).toMatch(
        /spatial-replay adapter raised an unexpected \(non-ENOENT\) error/i,
      );
      expect(warn).toHaveBeenCalled();
    } finally {
      warn.mockRestore();
    }
  });

  it("falls back to the 2D shell when both adapters throw", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    vi.mocked(loader.loadRehearsalAudit).mockRejectedValue(
      Object.assign(new Error("is a directory"), { code: "EISDIR" }),
    );
    vi.mocked(loader.loadSpatialReplay).mockRejectedValue(
      Object.assign(new Error("permission denied"), { code: "EACCES" }),
    );

    try {
      const Page = await WarehouseReplayDemoPage();
      render(Page);

      const reason =
        screen.getByTestId("demo-fallback-reason").textContent ?? "";
      expect(reason).toMatch(
        /rehearsal-audit and spatial-replay adapters both raised/i,
      );
    } finally {
      warn.mockRestore();
    }
  });

  it("never renders 'The mission replay demo could not load' for any loader failure", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    // Throw the most surprising thing we can: a non-Error value.
    vi.mocked(loader.loadRehearsalAudit).mockRejectedValue("boom");
    vi.mocked(loader.loadSpatialReplay).mockRejectedValue(
      Object.assign(new Error("EROFS"), { code: "EROFS" }),
    );

    try {
      const Page = await WarehouseReplayDemoPage();
      render(Page);

      const text = document.body.textContent ?? "";
      expect(text).not.toMatch(/The mission replay demo could not load/i);
      expect(text).toMatch(/2D fallback active/i);
    } finally {
      warn.mockRestore();
    }
  });
});
