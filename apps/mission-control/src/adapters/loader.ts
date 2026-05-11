import { promises as fs } from "node:fs";
import * as path from "node:path";

import type {
  LiveRuntimeMaturity,
  MissionLibraryEntry,
  MissionLibraryKind,
  RehearsalAudit,
  ReplayBundle,
  RequirementRow,
  SkillCardSummary,
  TraceabilitySummary,
  ValidationDiagnostic,
} from "./types";
import { repoPaths } from "./paths";

/**
 * Read a JSON file or return ``null`` when missing.
 *
 * The adapter NEVER fabricates contents on a missing file — callers
 * receive ``null`` so the UI can render an honest "no artefact"
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
// Rehearsal artefacts
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
