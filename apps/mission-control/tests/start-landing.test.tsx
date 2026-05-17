/**
 * Focused tests for the launch-quality /start landing page.
 *
 * These pin the public-facing contract the new hero/journey/
 * challenge/safety/proof composition has to keep:
 *
 *   - the mission-control headline is visible
 *   - the simulation-only / not-safety-certified boundary is visible
 *   - the primary CTA targets /demo/warehouse-replay
 *   - the secondary CTA targets /safety
 *   - the three Mission Challenge scenarios render
 *   - the six reviewer routes are still linked
 *   - no copy implies field certification or production deployment
 *
 * Animation details (framer-motion transitions, drei stuff, etc.) are
 * intentionally NOT asserted — those are implementation, and the
 * design-tokens / a11y / reviewer-experience suites already pin
 * style honesty separately.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  usePathname: () => "/start",
}));

vi.mock("@/adapters/loader", async () => {
  const actual: typeof import("@/adapters/loader") = await vi.importActual(
    "@/adapters/loader",
  );
  return {
    ...actual,
    loadRehearsalAudit: vi.fn(() => {
      throw new Error("loadRehearsalAudit must not be called from /start");
    }),
    loadSpatialReplay: vi.fn(() => {
      throw new Error("loadSpatialReplay must not be called from /start");
    }),
  };
});

import ReviewerStartPage from "@/app/start/page";

function renderStart() {
  return render(<ReviewerStartPage />);
}

describe("/start landing page", () => {
  it("renders the active mission-control headline", () => {
    renderStart();
    const h1 = screen.getByRole("heading", { level: 1 });
    const text = h1.textContent ?? "";
    expect(text).toMatch(/approved/i);
    expect(text).toMatch(/rejected/i);
    expect(text).toMatch(/replay/i);
  });

  it("keeps the simulation-only / not-safety-certified boundary visible", () => {
    renderStart();
    const body = document.body.textContent ?? "";
    expect(body).toMatch(/simulation only/i);
    expect(body).toMatch(/not safety[- ]certified/i);
    expect(body).toMatch(/does not control real hardware/i);
  });

  it("does not imply field certification or production deployment", () => {
    renderStart();
    const body = (document.body.textContent ?? "").toLowerCase();
    const FORBIDDEN_POSITIVE_CLAIMS = [
      "field certified",
      "field-certified",
      "production-ready rover",
      "production ready rover",
      "production-ready robot",
      "production ready robot",
      "deployed on real robots",
      "deployed to production rover",
      "fully autonomous in production",
      "ready for real-world deployment",
      "ready for real world deployment",
    ];
    for (const phrase of FORBIDDEN_POSITIVE_CLAIMS) {
      expect(body).not.toContain(phrase);
    }
    // The disclaimer says "not safety-certified". Confirm the only
    // mentions of "safety-certified" appear adjacent to "not".
    const certMentions = [...body.matchAll(/safety[- ]certified/g)];
    expect(certMentions.length).toBeGreaterThan(0);
    for (const m of certMentions) {
      const start = Math.max(0, (m.index ?? 0) - 6);
      const before = body.slice(start, m.index);
      expect(before).toMatch(/not\s*$/);
    }
  });

  it("primary CTA links to /demo/warehouse-replay and secondary CTA to /safety", () => {
    renderStart();
    const cta = screen.getByTestId("start-cta-demo");
    expect(cta).toHaveAttribute("href", "/demo/warehouse-replay");
    expect(cta.textContent ?? "").toMatch(/run.*mission replay/i);

    const safetyLinks = screen
      .getAllByRole("link")
      .filter((a) => a.getAttribute("href") === "/safety");
    expect(safetyLinks.length).toBeGreaterThan(0);
    expect(
      safetyLinks.some((a) =>
        /inspect safety authority/i.test(a.textContent ?? ""),
      ),
    ).toBe(true);
  });

  it("renders all three Mission Challenge scenario cards", () => {
    renderStart();
    const region = screen.getByTestId("mission-challenges");
    const text = region.textContent ?? "";
    expect(text).toMatch(/approved path/i);
    expect(text).toMatch(/boundary violation/i);
    expect(text).toMatch(/evidence review/i);
  });

  it("links every required reviewer route", () => {
    renderStart();
    const hrefs = screen
      .getAllByRole("link")
      .map((a) => a.getAttribute("href"));
    const required = [
      "/demo/warehouse-replay",
      "/safety",
      "/walkthrough",
      "/evidence",
      "/workspaces",
      "/workbench",
    ];
    for (const href of required) {
      expect(hrefs).toContain(href);
    }
  });

  it("renders the mission preview and an in-preview link to the full replay", () => {
    renderStart();
    const hero = screen.getByTestId("mission-hero");
    expect(within(hero).getByTestId("hero-sim-chip")).toBeInTheDocument();

    // HeroMissionPreview always renders a frame — the real 3D scene
    // when WebGL is available, the SVG AnimatedMissionPreview otherwise.
    // happy-dom has no WebGL, so the SVG fallback path is taken here.
    const preview = within(hero).getByTestId("hero-mission-preview");
    expect(preview).toBeInTheDocument();

    const previewCta = within(hero).getByTestId("hero-preview-cta");
    expect(previewCta).toHaveAttribute("href", "/demo/warehouse-replay");
    expect(previewCta.textContent ?? "").toMatch(/open full replay/i);
  });

  it("uses the recommended reviewer-journey step labels", () => {
    renderStart();
    const journey = screen.getByTestId("mission-journey");
    const text = journey.textContent ?? "";
    expect(text).toMatch(/run the replay/i);
    expect(text).toMatch(/inspect the supervisor/i);
    expect(text).toMatch(/trace the decision/i);
    expect(text).toMatch(/audit the evidence/i);
    expect(text).toMatch(/review the architecture/i);
  });

  it("renders the safety-authority pipeline preview", () => {
    renderStart();
    const region = screen.getByTestId("safety-authority-preview");
    const text = region.textContent ?? "";
    expect(text).toMatch(/proposed command/i);
    expect(text).toMatch(/validator/i);
    expect(text).toMatch(/supervisor/i);
    expect(text).toMatch(/approved.*rejected|rejected.*approved/i);
    expect(text).toMatch(/evidence/i);
  });

  it("renders the six-route reviewer directory", () => {
    renderStart();
    const region = screen.getByTestId("reviewer-routes");
    const hrefs = within(region)
      .getAllByRole("link")
      .map((a) => a.getAttribute("href"));
    expect(hrefs).toEqual(
      expect.arrayContaining([
        "/demo/warehouse-replay",
        "/safety",
        "/walkthrough",
        "/evidence",
        "/workspaces",
        "/workbench",
      ]),
    );
  });

  it("renders without invoking artifact loaders", async () => {
    const loader = await import("@/adapters/loader");
    expect(() => renderStart()).not.toThrow();
    expect(loader.loadRehearsalAudit).not.toHaveBeenCalled();
    expect(loader.loadSpatialReplay).not.toHaveBeenCalled();
  });
});
