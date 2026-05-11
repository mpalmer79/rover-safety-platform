import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { GradientPanel } from "@/components/GradientPanel";
import { PageSurface } from "@/components/PageSurface";
import { ResponsiveGrid } from "@/components/ResponsiveGrid";
import { SafetyBoundaryBanner } from "@/components/SafetyBoundaryBanner";

describe("PageSurface", () => {
  it("applies mobile-first padding + max-w-7xl cap", () => {
    render(
      <PageSurface>
        <p>content</p>
      </PageSurface>,
    );
    const surface = screen.getByTestId("page-surface");
    expect(surface.className).toMatch(/max-w-7xl/);
    expect(surface.className).toMatch(/px-3/);
    expect(surface.className).toMatch(/sm:px-5/);
    expect(surface.className).toMatch(/lg:px-8/);
  });

  it("renders the hero variant with the hero gradient", () => {
    render(
      <PageSurface variant="hero">
        <p>hero</p>
      </PageSurface>,
    );
    const surface = screen.getByTestId("page-surface");
    expect(surface.getAttribute("data-variant")).toBe("hero");
    expect(surface.className).toMatch(/surface-hero/);
  });
});

describe("ResponsiveGrid", () => {
  it("stack shape uses one column at every breakpoint", () => {
    render(
      <ResponsiveGrid shape="stack">
        <div />
      </ResponsiveGrid>,
    );
    const grid = screen.getByTestId("responsive-grid");
    expect(grid.className).toMatch(/grid-cols-1/);
    expect(grid.className).not.toMatch(/md:grid-cols-2/);
  });

  it("auto shape adds md:grid-cols-2 and xl:grid-cols-3", () => {
    render(
      <ResponsiveGrid shape="auto">
        <div />
      </ResponsiveGrid>,
    );
    const grid = screen.getByTestId("responsive-grid");
    expect(grid.className).toMatch(/md:grid-cols-2/);
    expect(grid.className).toMatch(/xl:grid-cols-3/);
  });

  it("mission shape collapses to a single column on small screens", () => {
    render(
      <ResponsiveGrid shape="mission">
        <div />
      </ResponsiveGrid>,
    );
    const grid = screen.getByTestId("responsive-grid");
    expect(grid.className).toMatch(/grid-cols-1/);
    expect(grid.className).toMatch(/md:grid-cols-2/);
  });
});

describe("GradientPanel tones", () => {
  it("renders the default neutral tone", () => {
    render(<GradientPanel>x</GradientPanel>);
    const panel = screen.getByTestId("gradient-panel");
    expect(panel.getAttribute("data-tone")).toBe("default");
  });

  it("renders the warning tone for pending callouts", () => {
    render(<GradientPanel tone="warning">x</GradientPanel>);
    const panel = screen.getByTestId("gradient-panel");
    expect(panel.getAttribute("data-tone")).toBe("warning");
  });

  it("does not apply pure-color bg-black / bg-white", () => {
    render(<GradientPanel>x</GradientPanel>);
    const panel = screen.getByTestId("gradient-panel");
    expect(panel.className).not.toMatch(/\bbg-black\b/);
    expect(panel.className).not.toMatch(/\bbg-white\b/);
  });
});

describe("Safety boundary banner remains visible", () => {
  it("renders the Simulation-only banner", () => {
    render(<SafetyBoundaryBanner />);
    expect(screen.getByText(/Simulation-only/i)).toBeInTheDocument();
  });
});
