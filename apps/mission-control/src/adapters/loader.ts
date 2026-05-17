import { promises as fs } from "node:fs";
import * as path from "node:path";

import type {
  ArtifactRegistry,
  ArtifactRegistryFile,
  ArtifactRegistryRecord,
  LiveRuntimeMaturity,
  MissionLibraryEntry,
  MissionLibraryKind,
  RehearsalAudit,
  ReplayBundle,
  RequirementRow,
  SkillCardSummary,
  SpatialReplayArtifact,
  SpatialReplayEventAlignment,
  SpatialReplayPoseSample,
  SpatialReplaySegment,
  TraceabilitySummary,
  ValidationDiagnostic,
} from "./types";
import { repoPaths } from "./paths";

/**
 * #17 trust-boundary helper: resolve a registry-controlled relative
 * path under ``repoRoot`` and refuse anything that escapes.
 *
 * Rules:
 * - reject paths that are absolute (start with ``/`` or a drive
 *   letter on Windows).
 * - reject paths that contain ``..`` segments before resolution.
 * - after ``path.resolve``, the result MUST start with
 *   ``repoRoot + path.sep``. Equality with ``repoRoot`` itself is also
 *   rejected — the registry should always point at a file, not the
 *   root.
 *
 * Returns ``null`` on rejection so callers can take the "honest no
 * artifact" path that already exists. Logs to the server-side console
 * because mission-control runs server-side in Next.js for the file
 * loader; a developer running ``next dev`` will see the rejection.
 */
export function resolveSafeRepoPath(
  repoRoot: string,
  relativePath: string,
): string | null {
  if (typeof relativePath !== "string" || relativePath.length === 0) {
    return null;
  }
  if (path.isAbsolute(relativePath)) {
    console.warn(
      `[loader] refusing absolute registry path: ${JSON.stringify(relativePath)}`,
    );
    return null;
  }
  // Reject any segment that is literally ``..`` (cross-platform).
  const segments = relativePath.split(/[/\\]/);
  if (segments.some((s) => s === "..")) {
    console.warn(
      `[loader] refusing registry path with .. segments: ${JSON.stringify(relativePath)}`,
    );
    return null;
  }
  const resolvedRoot = path.resolve(repoRoot);
  const absolute = path.resolve(resolvedRoot, relativePath);
  if (absolute === resolvedRoot) {
    return null;
  }
  if (!absolute.startsWith(resolvedRoot + path.sep)) {
    console.warn(
      `[loader] resolved path escapes repoRoot: ${JSON.stringify(absolute)}`,
    );
    return null;
  }
  return absolute;
}

/**
 * Read a JSON file or return ``null`` when missing.
 *
 * The adapter NEVER fabricates contents on a missing file — callers
 * receive ``null`` so the UI can render an honest "no artifact"
 * state. Honesty is preserved at the adapter boundary.
 */
async function readJson<T>(filePath: string): Promise<T | null> {
  try {
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw) as T;
  } catch (err) {
    const code = (err as NodeJS.ErrnoException).code;
    if (code === "ENOENT" || code === "ENOTDIR") {
      return null;
    }
    throw err;
  }
}

async function listSubdirs(dir: string): Promise<string[]> {
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
      .sort();
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      return [];
    }
    throw err;
  }
}

async function listJsonFiles(dir: string): Promise<string[]> {
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isFile() && entry.name.endsWith(".json"))
      .map((entry) => entry.name)
      .sort();
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      return [];
    }
    throw err;
  }
}

// ---------------------------------------------------------------------
// Rehearsal artifacts
// ---------------------------------------------------------------------

export async function listRehearsalIds(): Promise<readonly string[]> {
  const paths = repoPaths();
  return listSubdirs(paths.rehearsalAuditsDir);
}

export async function loadRehearsalAudit(
  exampleId: string,
): Promise<RehearsalAudit | null> {
  const paths = repoPaths();
  return readJson<RehearsalAudit>(paths.rehearsalAuditPath(exampleId));
}

export async function loadRehearsalAudits(): Promise<readonly RehearsalAudit[]> {
  const ids = await listRehearsalIds();
  const out: RehearsalAudit[] = [];
  for (const id of ids) {
    const audit = await loadRehearsalAudit(id);
    if (audit !== null) {
      out.push(audit);
    }
  }
  return out;
}

interface MissionExampleFile {
  example_id?: string;
  kind?: MissionLibraryKind | string;
  description?: string;
  mission_id?: string;
  request_id?: string;
  proposal_source?: string;
  waypoints?: unknown[];
  safety_constraints?: unknown[];
}

function coerceLibraryEntry(
  raw: MissionExampleFile,
): MissionLibraryEntry | null {
  if (!raw.example_id) return null;
  const kind: MissionLibraryKind = raw.kind === "rejected" ? "rejected" : "accepted";
  return {
    example_id: String(raw.example_id),
    kind,
    description: String(raw.description ?? ""),
    mission_id: String(raw.mission_id ?? raw.example_id),
    request_id: String(raw.request_id ?? raw.example_id),
    proposal_source: String(raw.proposal_source ?? ""),
    waypoints: ((raw.waypoints ?? []) as Array<Record<string, unknown>>).map((w) => ({
      waypoint_id: String(w.waypoint_id ?? ""),
      label: String(w.label ?? ""),
      stage_kind: String(w.stage_kind ?? "move"),
      bounded_distance_m: Number(w.bounded_distance_m ?? 0),
      bounded_angle_deg: Number(w.bounded_angle_deg ?? 0),
      bounded_speed_mps: Number(w.bounded_speed_mps ?? 0),
    })),
    safety_constraints: ((raw.safety_constraints ?? []) as unknown[]).map((s) =>
      String(s),
    ),
  };
}

export async function listMissionLibraryEntries(): Promise<readonly MissionLibraryEntry[]> {
  const paths = repoPaths();
  const names = await listJsonFiles(paths.rehearsalExamplesDir);
  const entries: MissionLibraryEntry[] = [];
  for (const name of names) {
    const data = await readJson<MissionExampleFile>(
      path.join(paths.rehearsalExamplesDir, name),
    );
    if (data) {
      const entry = coerceLibraryEntry(data);
      if (entry) entries.push(entry);
    }
  }
  return entries;
}

// ---------------------------------------------------------------------
// Skill library
// ---------------------------------------------------------------------

interface SkillFile {
  skill_id?: string;
  skill_type?: string;
  language?: string;
  title?: string;
  subtitle?: string;
  code?: string;
  code_card?: {
    safety_badges?: string[];
    animation_steps?: string[];
  };
  safety_review?: {
    risk_band?: string;
    safety_status?: string;
  };
  generated_at_utc?: string;
}

function coerceSkill(raw: SkillFile): SkillCardSummary | null {
  if (!raw.skill_id) return null;
  return {
    skill_id: String(raw.skill_id),
    skill_type: String(raw.skill_type ?? ""),
    language: String(raw.language ?? "python_ros2"),
    title: String(raw.title ?? ""),
    subtitle: String(raw.subtitle ?? ""),
    risk_band: String(raw.safety_review?.risk_band ?? "guarded"),
    safety_status: String(raw.safety_review?.safety_status ?? "needs_review"),
    generated_at_utc: String(raw.generated_at_utc ?? ""),
    code: String(raw.code ?? ""),
    code_card: {
      safety_badges: raw.code_card?.safety_badges ?? [],
      animation_steps: raw.code_card?.animation_steps ?? [],
    },
  };
}

export async function listSkillExampleIds(): Promise<readonly string[]> {
  const paths = repoPaths();
  return listSubdirs(paths.skillLibraryAuditsDir);
}

export async function loadSkillExample(
  exampleId: string,
): Promise<SkillCardSummary | null> {
  const paths = repoPaths();
  const data = await readJson<SkillFile>(paths.skillLibraryAuditPath(exampleId));
  return data ? coerceSkill(data) : null;
}

export async function loadAcceptedSkills(): Promise<readonly SkillCardSummary[]> {
  const ids = await listSkillExampleIds();
  const out: SkillCardSummary[] = [];
  for (const id of ids) {
    const skill = await loadSkillExample(id);
    if (skill) out.push(skill);
  }
  return out;
}

// ---------------------------------------------------------------------
// Traceability + verification report
// ---------------------------------------------------------------------

export async function loadTraceability(): Promise<TraceabilitySummary | null> {
  const paths = repoPaths();
  const data = await readJson<{
    generated_at_utc?: string;
    overall_status?: string;
    row_count?: number;
    rows?: Array<Record<string, unknown>>;
  }>(paths.traceabilityJson);
  if (!data) return null;
  const rows: RequirementRow[] = (data.rows ?? []).map((r) => ({
    req_id: String(r.requirement_id ?? r.req_id ?? ""),
    kind: String(r.kind ?? ""),
    title: String(r.title ?? ""),
    status: (r.status as RequirementRow["status"]) ?? "not_executed",
    status_detail: String(r.status_detail ?? ""),
    architecture_refs: (r.architecture_refs as string[] | undefined) ?? [],
    implementation_refs: (r.implementation_refs as string[] | undefined) ?? [],
    test_refs: (r.test_refs as string[] | undefined) ?? [],
    scenario_refs: (r.scenario_refs as string[] | undefined) ?? [],
    evidence_paths: (r.evidence_paths as string[] | undefined) ?? [],
  }));
  return {
    generated_at_utc: String(data.generated_at_utc ?? ""),
    overall_status:
      (data.overall_status as TraceabilitySummary["overall_status"]) ?? "not_executed",
    row_count: rows.length,
    rows,
  };
}

// ---------------------------------------------------------------------
// Live runtime maturity
// ---------------------------------------------------------------------

interface LiveMaturityRaw {
  generated_at_utc?: string;
  evidence_root?: string;
  runs_total?: number;
  latest_run_id?: string | null;
  latest_run_status?: string;
  runner_status?: string;
  status_counts?: Record<string, number>;
  bag_counters?: Record<string, number>;
  downstream?: Record<string, string>;
  known_limitations?: string[];
}

export async function loadLiveRuntimeMaturity(): Promise<LiveRuntimeMaturity | null> {
  const paths = repoPaths();
  const data = await readJson<LiveMaturityRaw>(paths.liveRuntimeMaturity);
  if (!data) return null;
  return {
    generated_at_utc: String(data.generated_at_utc ?? ""),
    evidence_root: String(data.evidence_root ?? ""),
    runs_total: Number(data.runs_total ?? 0),
    latest_run_id: data.latest_run_id ?? null,
    latest_run_status: String(data.latest_run_status ?? "unknown"),
    runner_status: String(data.runner_status ?? "unknown"),
    status_counts: data.status_counts ?? {},
    bag_counters: data.bag_counters ?? {},
    downstream: data.downstream ?? {},
    known_limitations: data.known_limitations ?? [],
  };
}

// ---------------------------------------------------------------------
// Convenience selectors
// ---------------------------------------------------------------------

export function summariseDiagnostics(
  diagnostics: readonly ValidationDiagnostic[],
): {
  rejection: number;
  warning: number;
  info: number;
} {
  let rejection = 0;
  let warning = 0;
  let info = 0;
  for (const d of diagnostics) {
    if (d.severity === "rejection") rejection += 1;
    else if (d.severity === "warning") warning += 1;
    else info += 1;
  }
  return { rejection, warning, info };
}

export function replayIsBagBacked(replay: ReplayBundle | null): boolean {
  return Boolean(replay && replay.bag_backed);
}

// ---------------------------------------------------------------------
// Phase 17C — spatial-replay artifact loader
// ---------------------------------------------------------------------

export {
  coerceSpatialReplayArtifact,
  type SpatialReplayRaw,
} from "./spatial-coerce";
import {
  coerceSpatialReplayArtifact,
  type SpatialReplayRaw,
} from "./spatial-coerce";

/**
 * Read the spatial-replay artifact for ``runId`` from disk.
 *
 * Phase 18: the loader consults the canonical artifact registry
 * before reading the file. If the registry exists and lists the
 * run, we trust the file path it points to and verify the artifact
 * is in an authoritative lifecycle state. If the registry is
 * missing (e.g. CI hasn't hydrated yet) the loader falls back to
 * the legacy filesystem-by-convention path so existing call sites
 * keep working.
 *
 * Returns ``null`` when the artifact is missing or malformed.
 */
export async function loadSpatialReplay(
  runId: string,
): Promise<SpatialReplayArtifact | null> {
  const paths = repoPaths();
  const registry = await loadArtifactRegistry();
  if (registry) {
    const record = registry.records.find((r) => r.run_id === runId);
    if (record) {
      if (record.lifecycle === "deprecated") {
        return null;
      }
      // Use the first registered ``spatial-replay.json`` if any.
      const file = record.files.find((f) =>
        f.relative_path.endsWith("spatial-replay.json"),
      );
      if (file) {
        // Anchor: spatialReplayRunsDir is ``<repoRoot>/spatial-replay/runs``.
        const repoRoot = path.resolve(paths.spatialReplayRunsDir, "..", "..");
        // ``relative_path`` is repo-rooted (e.g. ``spatial-replay/runs/<run>/...``).
        // #17 trust-boundary: the registry is on disk and notionally
        // checked in, but a tampered registry must not be able to
        // direct readJson at /etc/passwd. Reject absolute paths and
        // any ``..`` segments before resolution, and assert the final
        // absolute path stays under repoRoot.
        const resolved = resolveSafeRepoPath(repoRoot, file.relative_path);
        if (resolved !== null) {
          const raw = await readJson<SpatialReplayRaw>(resolved);
          if (raw) return coerceSpatialReplayArtifact(raw);
        }
      }
    }
  }
  // Legacy / fallback path.
  const raw = await readJson<SpatialReplayRaw>(paths.spatialReplayRunPath(runId));
  if (!raw) return null;
  return coerceSpatialReplayArtifact(raw);
}

/**
 * Return the list of available spatial-replay run ids.
 *
 * Prefers the registry; falls back to filesystem discovery.
 */
export async function listSpatialReplayRunIds(): Promise<readonly string[]> {
  const registry = await loadArtifactRegistry();
  if (registry) {
    return registry.records
      .filter(
        (r) =>
          r.lifecycle === "committed" ||
          r.lifecycle === "verified" ||
          r.lifecycle === "canonical",
      )
      .map((r) => r.run_id);
  }
  const paths = repoPaths();
  return listSubdirs(paths.spatialReplayRunsDir);
}

// ---------------------------------------------------------------------
// Phase 18 — artifact registry
// ---------------------------------------------------------------------

interface ArtifactRegistryRaw {
  generated_at_utc?: string;
  schema_version?: string;
  artefact_root?: string;
  notes?: string[];
  records?: Array<Record<string, unknown>>;
}

function coerceRegistryFile(raw: Record<string, unknown>): ArtifactRegistryFile {
  return {
    relative_path: String(raw.relative_path ?? ""),
    expected_hash: String(raw.expected_hash ?? ""),
    size_bytes: Number(raw.size_bytes ?? 0),
    description: String(raw.description ?? ""),
  };
}

function coerceRegistryRecord(
  raw: Record<string, unknown>,
): ArtifactRegistryRecord {
  const filesRaw = (raw.files as Array<Record<string, unknown>>) ?? [];
  return {
    run_id: String(raw.run_id ?? ""),
    kind: String(raw.kind ?? ""),
    derivation_source: String(raw.derivation_source ?? "unavailable") as
      ArtifactRegistryRecord["derivation_source"],
    bag_status: String(raw.bag_status ?? "missing_manifest") as
      ArtifactRegistryRecord["bag_status"],
    lifecycle: String(raw.lifecycle ?? "generated") as
      ArtifactRegistryRecord["lifecycle"],
    integrity: String(raw.integrity ?? "unverified") as
      ArtifactRegistryRecord["integrity"],
    related_mission_id: String(raw.related_mission_id ?? ""),
    related_scenario_id: String(raw.related_scenario_id ?? ""),
    notes: ((raw.notes as string[]) ?? []).map(String),
    generated_at_utc: String(raw.generated_at_utc ?? ""),
    files: filesRaw.map(coerceRegistryFile),
  };
}

/**
 * Read the canonical artifact registry from disk.
 *
 * Returns ``null`` when missing — Phase 18 frontend code paths
 * gracefully degrade to the legacy filesystem-by-convention path.
 */
export async function loadArtifactRegistry(): Promise<ArtifactRegistry | null> {
  const paths = repoPaths();
  const raw = await readJson<ArtifactRegistryRaw>(paths.artifactRegistryJson);
  if (!raw || !Array.isArray(raw.records)) return null;
  return {
    generated_at_utc: String(raw.generated_at_utc ?? ""),
    schema_version: String(raw.schema_version ?? ""),
    artefact_root: String(raw.artefact_root ?? "spatial-replay"),
    notes: (raw.notes ?? []).map(String),
    records: raw.records.map(coerceRegistryRecord),
  };
}

export async function loadArtifactRegistryRecord(
  runId: string,
): Promise<ArtifactRegistryRecord | null> {
  const reg = await loadArtifactRegistry();
  if (!reg) return null;
  return reg.records.find((r) => r.run_id === runId) ?? null;
}
