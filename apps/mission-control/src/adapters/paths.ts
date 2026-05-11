import * as path from "node:path";

/**
 * Resolve the repository root from anywhere inside ``apps/mission-control``.
 *
 * The mission-control workspace lives at ``<repo>/apps/mission-control``;
 * the adapters read JSON artefacts from sibling directories such as
 * ``<repo>/mission-rehearsals`` and ``<repo>/verification``. Anchoring
 * to the workspace's own location keeps the adapters deterministic
 * regardless of where Next.js was invoked from.
 */
export function repoRoot(): string {
  // ``__dirname`` inside the compiled build resolves to a path under
  // ``.next/server/...``; the source root is the only thing we can
  // reliably pin to without a runtime env var.
  return path.resolve(process.cwd(), "..", "..");
}

export interface RepoPaths {
  rehearsalAuditsDir: string;
  rehearsalExamplesDir: string;
  rehearsalAuditPath: (exampleId: string) => string;
  skillLibraryAuditsDir: string;
  skillLibraryAuditPath: (exampleId: string) => string;
  missionProposalsAuditsDir: string;
  traceabilityJson: string;
  verificationReportJson: string;
  liveRuntimeMaturity: string;
  spatialReplayRunsDir: string;
  spatialReplayRunPath: (runId: string) => string;
  artifactRegistryJson: string;
  hydrationReportJson: string;
}

export function repoPaths(root: string = repoRoot()): RepoPaths {
  return {
    rehearsalAuditsDir: path.join(root, "mission-rehearsals", "audits"),
    rehearsalExamplesDir: path.join(root, "mission-rehearsals", "examples"),
    rehearsalAuditPath: (id: string) =>
      path.join(root, "mission-rehearsals", "audits", id, "rehearsal-audit.json"),
    skillLibraryAuditsDir: path.join(root, "skill-library", "audits"),
    skillLibraryAuditPath: (id: string) =>
      path.join(root, "skill-library", "audits", id, "generated-skill.json"),
    missionProposalsAuditsDir: path.join(root, "mission-proposals", "audits"),
    traceabilityJson: path.join(root, "verification", "traceability.json"),
    verificationReportJson: path.join(root, "verification", "verification_report.json"),
    liveRuntimeMaturity: path.join(root, "live-runtime", "live-runtime-maturity.json"),
    spatialReplayRunsDir: path.join(root, "spatial-replay", "runs"),
    spatialReplayRunPath: (runId: string) =>
      path.join(root, "spatial-replay", "runs", runId, "spatial-replay.json"),
    artifactRegistryJson: path.join(
      root,
      "spatial-replay",
      "registry",
      "canonical-artifacts.json",
    ),
    hydrationReportJson: path.join(
      root,
      "spatial-replay",
      "registry",
      "hydration-report.json",
    ),
  };
}
