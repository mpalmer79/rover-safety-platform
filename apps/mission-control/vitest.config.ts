import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import * as path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "happy-dom",
    globals: true,
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
    setupFiles: ["./tests/setup.ts"],
    // ---------------------------------------------------------------
    // Coverage gating (Item 1).
    //
    // Pinned floors are HONEST current floors, not aspirational
    // targets. The global threshold is (observed - 2). Per-file
    // floors on safety-relevant components are stricter; if a
    // safety-relevant file is below 95% today, its floor is pinned
    // at (observed - 1) with a remediation note in README.md.
    // ---------------------------------------------------------------
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "json-summary", "lcov"],
      reportsDirectory: "./coverage",
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.test.*",
        "src/**/types.ts",
        "src/3d/**",
      ],
      // Global floor: pinned (observed - 2) on each metric. The
      // values below reflect the most recent honest baseline (see
      // README.md "Coverage gating" for the full history).
      //
      // Item 1 baseline:  lines 59.82, statements 59.82,
      //                   functions 77.96, branches 63.40.
      // Item 2 baseline:  lines 59.70, statements 59.70,
      //                   functions 74.80, branches 64.26.
      //                   (Adding loading.tsx + error.tsx + not-
      //                   found.tsx + 6×route variants added ~18
      //                   functions; only error.tsx is exercised by
      //                   tests, so functions dropped.)
      thresholds: {
        lines: 57,
        statements: 57,
        functions: 72,
        branches: 61,
        perFile: false,
        // Per-file floors on safety-relevant components. The
        // canonical target is 95% lines + statements + functions,
        // 90% branches. Any file below that target today is pinned
        // at (observed - 1) and noted as remediation in
        // README.md "Coverage gating > Remediation".
        "src/components/SupervisorAuthorityPanel.tsx": {
          // observed 0% — file is not yet exercised by any test.
          // Remediation: add a test that renders the panel with a
          // sample SupervisorDecision and asserts the rationale +
          // rejected_reasons render verbatim.
          lines: 0,
          statements: 0,
          functions: 0,
          branches: 0,
        },
        "src/components/SafetyBoundaryBanner.tsx": {
          // observed 100% — meets the canonical floor.
          lines: 95,
          statements: 95,
          functions: 95,
          branches: 90,
        },
        "src/components/SupervisorInterventionOverlay.tsx": {
          // observed lines 100, branches 80.
          // Remediation: add a test for the supervisor-specific
          // event-subtype branch.
          lines: 95,
          statements: 95,
          functions: 95,
          branches: 79,
        },
        "src/components/EvidenceStatusChip.tsx": {
          // observed lines 100, branches 20.
          // Remediation: add tests for every (status, bagBacked)
          // pair; today only one combination is covered.
          lines: 95,
          statements: 95,
          functions: 95,
          branches: 19,
        },
        "src/components/RequirementBadge.tsx": {
          // observed lines 100, branches 66.66.
          // Remediation: cover the not_executed status branch.
          lines: 95,
          statements: 95,
          functions: 95,
          branches: 65,
        },
        "src/adapters/loader.ts": {
          // observed lines 90.52, branches 36.07.
          // Remediation: cover the deprecated-record-skipped branch
          // in loadSpatialReplay + the legacy filesystem-fallback
          // path.
          lines: 89,
          statements: 89,
          functions: 95,
          branches: 35,
        },
      },
    },
  },
});
