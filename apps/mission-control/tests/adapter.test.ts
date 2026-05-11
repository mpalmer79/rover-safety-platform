import { describe, it, expect } from "vitest";

import {
  listMissionLibraryEntries,
  listRehearsalIds,
  loadRehearsalAudit,
  loadRehearsalAudits,
  loadTraceability,
  loadAcceptedSkills,
  replayIsBagBacked,
  summariseDiagnostics,
} from "../src/adapters/loader";

describe("rehearsal audit adapters", () => {
  it("lists every committed rehearsal id", async () => {
    const ids = await listRehearsalIds();
    expect(ids).toEqual([
      "bounded_forward_patrol",
      "direct_motor_override",
      "disable_supervisor_attempt",
      "emergency_stop_rehearsal",
      "infinite_patrol_loop",
      "inspection_lane_beta",
      "restricted_zone_entry",
      "unsafe_speed_route",
      "warehouse_pickup_route_alpha",
      "waypoint_delivery_alpha",
    ]);
  });

  it("loads a completed audit verbatim", async () => {
    const audit = await loadRehearsalAudit("warehouse_pickup_route_alpha");
    expect(audit).not.toBeNull();
    expect(audit!.final_status).toBe("completed");
    // Phase 16 reports `guarded` for risk-band='guarded' plans even
    // when the runtime completed; the adapter passes that through
    // verbatim and never silently upgrades the safety status.
    expect(["safe", "guarded"]).toContain(audit!.safety_status);
    expect(audit!.replay).not.toBeNull();
    expect(audit!.replay!.bag_backed).toBe(false);
    expect(audit!.replay!.evidence_status).toBe("simulated");
  });

  it("preserves rejection reasons", async () => {
    const audit = await loadRehearsalAudit("unsafe_speed_route");
    expect(audit).not.toBeNull();
    expect(audit!.final_status).toBe("rejected");
    expect(audit!.final_failure_reason).toBe("unsafe_speed");
  });

  it("returns null for unknown audits", async () => {
    const audit = await loadRehearsalAudit("definitely-not-real");
    expect(audit).toBeNull();
  });

  it("loads all audits in stable order", async () => {
    const audits = await loadRehearsalAudits();
    expect(audits.length).toBeGreaterThanOrEqual(10);
    for (const audit of audits) {
      // Honesty assertion: every replay bundle is simulation-only.
      if (audit.replay) {
        expect(audit.replay.bag_backed).toBe(false);
        expect(audit.replay.evidence_status).toBe("simulated");
      }
    }
  });
});

describe("mission library", () => {
  it("loads the canonical 10 example files", async () => {
    const entries = await listMissionLibraryEntries();
    expect(entries.length).toBe(10);
    expect(entries.filter((e) => e.kind === "accepted").length).toBe(5);
    expect(entries.filter((e) => e.kind === "rejected").length).toBe(5);
  });
});

describe("skill library", () => {
  it("loads accepted skills with code cards", async () => {
    const skills = await loadAcceptedSkills();
    expect(skills.length).toBeGreaterThan(0);
    for (const skill of skills) {
      expect(skill.code).not.toContain("\nimport socket");
      expect(skill.code_card.safety_badges).toContain("not-safety-certified");
    }
  });

  it("the move_forward_6_feet skill converts to 1.8288 m", async () => {
    const skills = await loadAcceptedSkills();
    const move = skills.find((s) => s.skill_id === "skill-move_forward_6_feet");
    expect(move).toBeDefined();
    expect(move!.code).toContain("DISTANCE_M = 1.8288");
    expect(move!.code).toContain("/cmd_vel_requested");
  });
});

describe("traceability", () => {
  it("reads the committed traceability JSON", async () => {
    const trace = await loadTraceability();
    expect(trace).not.toBeNull();
    expect(trace!.row_count).toBeGreaterThan(70);
    expect(trace!.overall_status).toBe("passed");
  });
});

describe("selectors", () => {
  it("summariseDiagnostics counts every severity", () => {
    expect(
      summariseDiagnostics([
        { code: "x", severity: "rejection", message: "" },
        { code: "y", severity: "warning", message: "" },
        { code: "z", severity: "info", message: "" },
      ]),
    ).toEqual({ rejection: 1, warning: 1, info: 1 });
  });

  it("replayIsBagBacked is false for null replays", () => {
    expect(replayIsBagBacked(null)).toBe(false);
  });
});
