import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { ThemeProvider, useTheme } from "@/lib/theme-provider";
import { ThemeToggle } from "@/components/ThemeToggle";

function Harness({ onMount }: { onMount?: (api: ReturnType<typeof useTheme>) => void }) {
  const api = useTheme();
  if (onMount) onMount(api);
  return <div data-testid="theme-current">{api.theme}</div>;
}

describe("ThemeProvider + useTheme", () => {
  let originalMatchMedia: typeof window.matchMedia;

  beforeEach(() => {
    document.documentElement.className = "";
    window.localStorage.clear();
    // Stub matchMedia: happy-dom defaults to
    // `prefers-color-scheme: light = true`, the opposite of the
    // platform's default. Force "no system preference" so the
    // provider falls through to DEFAULT_THEME = "dark".
    originalMatchMedia = window.matchMedia;
    window.matchMedia = vi.fn().mockReturnValue({
      matches: false,
      media: "",
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
      onchange: null,
    }) as unknown as typeof window.matchMedia;
  });

  afterEach(() => {
    document.documentElement.className = "";
    window.matchMedia = originalMatchMedia;
  });

  it("resolves the dark theme by default when no preference exists", () => {
    render(
      <ThemeProvider>
        <Harness />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("theme-current").textContent).toBe("dark");
  });

  it("toggle flips between dark and light and persists the choice", () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
        <Harness />
      </ThemeProvider>,
    );
    const toggle = screen.getByTestId("theme-toggle");
    expect(toggle.getAttribute("data-theme")).toBe("dark");
    fireEvent.click(toggle);
    expect(toggle.getAttribute("data-theme")).toBe("light");
    expect(window.localStorage.getItem("mc-theme-preference")).toBe("light");
    fireEvent.click(toggle);
    expect(toggle.getAttribute("data-theme")).toBe("dark");
    expect(window.localStorage.getItem("mc-theme-preference")).toBe("dark");
  });

  it("respects a stored preference on mount", () => {
    window.localStorage.setItem("mc-theme-preference", "light");
    render(
      <ThemeProvider>
        <Harness />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("theme-current").textContent).toBe("light");
  });

  it("ThemeToggle has aria-label describing the next state", () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );
    const toggle = screen.getByTestId("theme-toggle");
    expect(toggle.getAttribute("aria-label")).toMatch(/Switch to light theme/i);
    fireEvent.click(toggle);
    expect(toggle.getAttribute("aria-label")).toMatch(/Switch to dark theme/i);
  });

  it("ThemeToggle is accessible via keyboard (role=switch)", () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );
    const toggle = screen.getByTestId("theme-toggle");
    expect(toggle.getAttribute("role")).toBe("switch");
    expect(toggle.getAttribute("aria-checked")).toBe("true");
  });

  it("ThemeToggle medium emphasis renders a larger track", () => {
    render(
      <ThemeProvider>
        <ThemeToggle emphasis="medium" />
      </ThemeProvider>,
    );
    const toggle = screen.getByTestId("theme-toggle");
    expect(toggle.className).toMatch(/text-sm/);
  });

  it("toggle does not flash pure black/white during load", () => {
    // The bootstrap script applies a class before paint. In tests
    // we just confirm that the ThemeProvider never sets the html
    // background to '#000' or '#fff' directly.
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );
    const computed = window.getComputedStyle(document.documentElement);
    expect(computed.backgroundColor).not.toBe("rgb(0, 0, 0)");
    expect(computed.backgroundColor).not.toBe("rgb(255, 255, 255)");
  });
});
