/**
 * Trust-boundary test (#17): the registry-controlled relative_path
 * must not be allowed to escape the repo root via `..` segments,
 * absolute paths, or Windows-style drive letters / backslashes.
 *
 * The check is implemented in `resolveSafeRepoPath`; we exercise it
 * directly with a fixed `repoRoot` so the test does not depend on
 * the current working directory.
 */

import * as path from "node:path";
import { describe, it, expect } from "vitest";

import { resolveSafeRepoPath } from "@/adapters/loader";

const REPO_ROOT = path.resolve("/tmp/fake-repo-root");

describe("resolveSafeRepoPath", () => {
  it("accepts a normal repo-rooted relative path", () => {
    const out = resolveSafeRepoPath(
      REPO_ROOT,
      "spatial-replay/runs/canonical-fixture/spatial-replay.json",
    );
    expect(out).toBe(
      path.join(
        REPO_ROOT,
        "spatial-replay/runs/canonical-fixture/spatial-replay.json",
      ),
    );
  });

  it("rejects an absolute path", () => {
    expect(resolveSafeRepoPath(REPO_ROOT, "/etc/passwd")).toBeNull();
  });

  it("rejects parent-traversal segments", () => {
    expect(
      resolveSafeRepoPath(REPO_ROOT, "../../etc/passwd"),
    ).toBeNull();
    expect(
      resolveSafeRepoPath(REPO_ROOT, "spatial-replay/../../../etc/passwd"),
    ).toBeNull();
  });

  it("rejects Windows-style backslash traversal", () => {
    expect(
      resolveSafeRepoPath(REPO_ROOT, "..\\..\\windows\\system32"),
    ).toBeNull();
  });

  it("rejects an empty path", () => {
    expect(resolveSafeRepoPath(REPO_ROOT, "")).toBeNull();
  });

  it("rejects a path that resolves to the repo root itself", () => {
    expect(resolveSafeRepoPath(REPO_ROOT, ".")).toBeNull();
  });
});
