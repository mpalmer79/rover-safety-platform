/**
 * Warehouse Mission Replay server-page guarantees.
 *
 * The demo route is reviewer-facing. The page bundles its canonical
 * artifacts at build time so the prerender never depends on the
 * filesystem; the route error boundary must never appear in
 * production for this route.
 *
 * These tests exercise the page's server-side rendering path
 * directly. The 3D scene under WarehouseReplayDemo is covered by
 * tests/warehouse-replay-demo.test.tsx.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  usePathname: () => "/demo/warehouse-replay",
}));

import WarehouseReplayDemoPage from "@/app/demo/warehouse-replay/page";

describe("/demo/warehouse-replay server page", () => {
  it("renders the bundled canonical demo without touching the filesystem", () => {
    const Page = WarehouseReplayDemoPage();
    render(Page);

    expect(
      screen.getByRole("heading", { level: 1, name: /Warehouse pickup/i }),
    ).toBeInTheDocument();
  });

  it("never renders the route error boundary or 2D fallback copy", () => {
    const Page = WarehouseReplayDemoPage();
    render(Page);

    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(/The mission replay demo could not load/i);
    expect(text).not.toMatch(/2D fallback active/i);
  });
});
