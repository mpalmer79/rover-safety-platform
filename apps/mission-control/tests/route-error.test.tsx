import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import DashboardError from "@/app/error";
import WorkbenchError from "@/app/workbench/error";
import SafetyError from "@/app/safety/error";
import ReplayError from "@/app/replay/error";
import EvidenceError from "@/app/evidence/error";
import MissionDetailError from "@/app/missions/[id]/error";

const ERROR_PAGES: ReadonlyArray<{
  name: string;
  Component: (props: {
    error: Error & { digest?: string };
    reset: () => void;
  }) => React.JSX.Element;
}> = [
  { name: "/", Component: DashboardError },
  { name: "/workbench", Component: WorkbenchError },
  { name: "/safety", Component: SafetyError },
  { name: "/replay", Component: ReplayError },
  { name: "/evidence", Component: EvidenceError },
  { name: "/missions/[id]", Component: MissionDetailError },
];

describe("route error.tsx", () => {
  it.each(ERROR_PAGES)(
    "$name renders the digest and a working retry button",
    ({ Component }) => {
      const reset = vi.fn();
      const err = Object.assign(new Error("simulated"), {
        digest: "abc123-deterministic-digest",
      });
      render(<Component error={err} reset={reset} />);
      const digest = screen.getByTestId("route-error-digest");
      expect(digest.textContent).toBe("abc123-deterministic-digest");
      const retry = screen.getByTestId("route-error-retry");
      expect(retry.textContent).toMatch(/Retry/);
      fireEvent.click(retry);
      expect(reset).toHaveBeenCalledTimes(1);
    },
  );

  it.each(ERROR_PAGES)(
    "$name shows '(none)' when no digest is present",
    ({ Component }) => {
      const reset = vi.fn();
      render(<Component error={new Error("no digest")} reset={reset} />);
      const digest = screen.getByTestId("route-error-digest");
      expect(digest.textContent).toBe("(none)");
    },
  );

  it.each(ERROR_PAGES)(
    "$name does NOT use the wording 'something went wrong'",
    ({ Component }) => {
      const reset = vi.fn();
      const { container } = render(
        <Component error={new Error("simulated")} reset={reset} />,
      );
      expect(container.textContent ?? "").not.toMatch(/something went wrong/i);
    },
  );
});
