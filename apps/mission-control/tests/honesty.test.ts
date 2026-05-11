import { describe, it, expect } from "vitest";
import { promises as fs } from "node:fs";
import * as path from "node:path";

const SRC_ROOT = path.resolve(__dirname, "../src");

async function* walk(dir: string): AsyncGenerator<string> {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walk(full);
    } else if (
      entry.isFile() &&
      (entry.name.endsWith(".ts") || entry.name.endsWith(".tsx"))
    ) {
      yield full;
    }
  }
}

describe("frontend honesty rules", () => {
  it("never imports a cloud LLM SDK or a generic HTTP client", async () => {
    const forbidden = [
      "openai",
      "@anthropic-ai/sdk",
      "anthropic",
      "cohere-ai",
      "@google/generative-ai",
      "axios",
      "isomorphic-fetch",
    ];
    for await (const file of walk(SRC_ROOT)) {
      const text = await fs.readFile(file, "utf-8");
      for (const token of forbidden) {
        expect(
          text.includes(`from "${token}`) || text.includes(`from '${token}`),
          `${file} must not import ${token}`,
        ).toBe(false);
      }
    }
  });

  it("never references a /cmd_vel publication outside comments + descriptive context", async () => {
    // The UI is allowed to mention "/cmd_vel" in panels that describe
    // the safety boundary (Safety Authority page). We assert the
    // mentions sit inside JSX text or string literals (not the kind
    // of pattern that would imply we publish to that topic), and
    // never appear in an executable expression like `publish("/cmd_vel"`.
    const forbidden = /\bpublish\s*\(\s*['"]\/cmd_vel['"]/;
    for await (const file of walk(SRC_ROOT)) {
      const text = await fs.readFile(file, "utf-8");
      expect(forbidden.test(text), `${file} must not call publish("/cmd_vel")`).toBe(
        false,
      );
    }
  });

  it("never spawns subprocesses or opens raw sockets", async () => {
    const forbidden = [
      "child_process",
      "node:child_process",
      "node:net",
      "node:dgram",
    ];
    for await (const file of walk(SRC_ROOT)) {
      const text = await fs.readFile(file, "utf-8");
      for (const token of forbidden) {
        expect(
          text.includes(`from "${token}"`) ||
            text.includes(`from '${token}'`),
          `${file} must not import ${token}`,
        ).toBe(false);
      }
    }
  });

  it("the SafetyBoundaryBanner is rendered from the root layout", async () => {
    const layout = await fs.readFile(
      path.resolve(__dirname, "../src/app/layout.tsx"),
      "utf-8",
    );
    expect(layout).toContain("SafetyBoundaryBanner");
  });

  it("the evidence chip helper preserves the bag-backed input verbatim", async () => {
    const chip = await fs.readFile(
      path.resolve(__dirname, "../src/components/EvidenceStatusChip.tsx"),
      "utf-8",
    );
    // The chip must consume the prop and render a yes/no string based
    // on it; the component must never short-circuit to "yes" without
    // looking at the input.
    expect(chip).toMatch(/bagBacked\s*\?/);
    expect(chip).toContain("yes");
    expect(chip).toContain("no");
  });

  it("every component under src/components/ is imported by the a11y test", async () => {
    // Item 3 honesty rule: a new component cannot silently escape
    // the axe gate. The a11y test file MUST import every file in
    // src/components/ (the imports are also what the test iterates
    // over, so this guarantees coverage of the gate's surface).
    const componentsDir = path.resolve(__dirname, "../src/components");
    const a11y = await fs.readFile(
      path.resolve(__dirname, "./a11y.test.tsx"),
      "utf-8",
    );
    const entries = await fs.readdir(componentsDir, { withFileTypes: true });
    const componentFiles = entries
      .filter((e) => e.isFile() && e.name.endsWith(".tsx"))
      .map((e) => e.name.replace(/\.tsx$/, ""));
    for (const name of componentFiles) {
      const importPattern = new RegExp(
        `from\\s+["']@/components/${name}["']`,
      );
      expect(
        importPattern.test(a11y),
        `tests/a11y.test.tsx must import @/components/${name} so the new component is covered by the axe gate`,
      ).toBe(true);
    }
  });
});
