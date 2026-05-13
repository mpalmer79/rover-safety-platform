/**
 * Reviewer-experience guarantees.
 *
 * These tests pin the public-facing contract surfaced to recruiters,
 * hiring managers, and technical reviewers:
 *
 *   - the primary navigation contains the Start Here entry point
 *     and the Mission Replay Demo;
 *   - the public chrome no longer announces "Phase 19" /
 *     "Phase 17A" as the platform's identity;
 *   - the not-found fallback is reviewer-friendly (no internal
 *     pipeline language, links back to curated routes);
 *   - the Start Here landing page articulates what ProjectBoundary
 *     demonstrates and where to click first;
 *   - the safety-boundary banner combines the simulation-only
 *     boundary with what the platform demonstrates.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

vi.mock("@/adapters/loader", () => ({
  loadRehearsalAudit: vi.fn(async () => null),
  loadSpatialReplay: vi.fn(async () => null),
}));

import NotFound from "@/app/not-found";
import ReviewerHomePage from "@/app/page";
import { ResponsiveShell } from "@/components/ResponsiveShell";
import { SafetyBoundaryBanner } from "@/components/SafetyBoundaryBanner";

describe("public navigation chrome", () => {
  it("includes Start Here, Mission Replay Demo, and Safety Authority links", () => {
    render(
      <ResponsiveShell>
        <p>main</p>
      </ResponsiveShell>,
    );
    const sidebar = screen.getByTestId("primary-sidebar");
    const links = within(sidebar).getAllByRole("link");
    const hrefs = links.map((a) => a.getAttribute("href"));
    expect(hrefs).toContain("/");
    expect(hrefs).toContain("/demo/warehouse-replay");
    expect(hrefs).toContain("/safety");
    expect(hrefs).toContain("/walkthrough");
    expect(hrefs).toContain("/evidence");
  });

  it("places Start Here at the top of the navigation", () => {
    render(
      <ResponsiveShell>
        <p>main</p>
      </ResponsiveShell>,
    );
    const sidebar = screen.getByTestId("primary-sidebar");
    const items = within(sidebar)
      .getAllByRole("link")
      .filter((a) => {
        const href = a.getAttribute("href") ?? "";
        return href.startsWith("/") && href !== "/";
      });
    // The first reviewer destination after the brand link should be
    // a primary-flow route (Start Here, Mission Replay Demo, Safety
    // Authority, Walkthrough, Evidence) rather than Workbench/Catalog.
    const firstNavHref = within(sidebar)
      .getAllByRole("link")
      .map((a) => a.getAttribute("href"))
      .find((h) => h && h !== "/");
    expect(["/", "/demo/warehouse-replay"]).toContain(firstNavHref ?? "");
    expect(items.length).toBeGreaterThan(0);
  });

  it("does not announce internal phase labels as the public identity", () => {
    render(
      <ResponsiveShell>
        <p>main</p>
      </ResponsiveShell>,
    );
    const sidebar = screen.getByTestId("primary-sidebar");
    expect(sidebar.textContent ?? "").not.toMatch(/Phase 19/);
    expect(sidebar.textContent ?? "").not.toMatch(/Phase 17A/);
    expect(sidebar.textContent ?? "").not.toMatch(/Phase 14A/);
  });
});

describe("safety boundary banner", () => {
  it("communicates simulation-only AND what the platform demonstrates", () => {
    render(<SafetyBoundaryBanner />);
    const banner = screen.getByTestId("safety-boundary-banner");
    const text = banner.textContent ?? "";
    expect(text).toMatch(/simulation-only/i);
    expect(text).toMatch(/not safety-certified/i);
    expect(text).toMatch(/deterministic mission validation/i);
    expect(text).toMatch(/safety-supervisor authority/i);
  });

  it("does not control real hardware claim is preserved", () => {
    render(<SafetyBoundaryBanner />);
    const banner = screen.getByTestId("safety-boundary-banner");
    expect(banner.textContent ?? "").toMatch(/does not control real hardware/i);
  });
});

describe("not-found fallback", () => {
  it("does not expose internal artifact pipeline language", () => {
    render(<NotFound />);
    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(/No artifact at this path/i);
    expect(text).not.toMatch(/static export resolves every route/i);
  });

  it("offers reviewer-safe paths back into the demo", () => {
    render(<NotFound />);
    const list = screen.getByTestId("route-not-found");
    const links = within(list).getAllByRole("link");
    const hrefs = links.map((a) => a.getAttribute("href"));
    expect(hrefs).toContain("/");
    expect(hrefs).toContain("/demo/warehouse-replay");
    expect(hrefs).toContain("/safety");
    expect(hrefs).toContain("/walkthrough");
    expect(hrefs).toContain("/evidence");
  });
});

describe("Reviewer entry-point home page", () => {
  it("renders the Start Here heading and reviewer summary", async () => {
    const Page = await ReviewerHomePage();
    render(Page);
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /What ProjectBoundary demonstrates/i,
      }),
    ).toBeInTheDocument();
    const proves = screen.getByTestId("start-what-proves");
    const text = proves.textContent ?? "";
    expect(text).toMatch(/Unsafe motion requests are rejected/i);
    expect(text).toMatch(/Approved missions are deterministically replayable/i);
    expect(text).toMatch(/cannot bypass the safety supervisor/i);
  });

  it("links to the Mission Replay Demo, Safety Authority, Walkthrough, and Evidence", async () => {
    const Page = await ReviewerHomePage();
    render(Page);
    const links = screen.getAllByRole("link");
    const hrefs = links.map((a) => a.getAttribute("href"));
    expect(hrefs).toContain("/demo/warehouse-replay");
    expect(hrefs).toContain("/safety");
    expect(hrefs).toContain("/walkthrough");
    expect(hrefs).toContain("/evidence");
  });

  it("contains the explicit simulation-only / not safety-certified scope", async () => {
    const Page = await ReviewerHomePage();
    render(Page);
    const text = document.body.textContent ?? "";
    expect(text).toMatch(/simulation-only/i);
    expect(text).toMatch(/not safety-certified/i);
    expect(text).toMatch(/does not control real hardware/i);
  });
});
