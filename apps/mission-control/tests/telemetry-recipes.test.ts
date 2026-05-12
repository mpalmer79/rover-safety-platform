/**
 * Phase 20B telemetry recipe tests.
 *
 * Asserts that every recipe:
 *   * declares its required + optional artefact kinds;
 *   * returns ``unavailable`` when required inputs are missing;
 *   * never fabricates values;
 *   * preserves derivation_source / bag_backed verbatim.
 */

import { describe, it, expect } from "vitest";

import { RECIPE_IDS, RECIPE_REGISTRY, recipe } from "@/telemetry-recipes";
import {
  FIX_AUDIT,
  FIX_EVENT_INFO,
  FIX_PLAN,
  FIX_REGISTRY_RECORD,
  FIX_SPATIAL_ARTIFACT,
} from "@/components/__fixtures__/_shared";

describe("telemetry recipe registry", () => {
  it("exposes nine canonical recipes", () => {
    expect(RECIPE_IDS.length).toBe(9);
  });

  it("every recipe id resolves", () => {
    for (const id of RECIPE_IDS) {
      const r = recipe(id);
      expect(r, id).not.toBeNull();
      expect(r?.recipeId).toBe(id);
    }
  });

  it("unknown recipe ids return null", () => {
    expect(recipe("not-a-recipe")).toBeNull();
  });
});

describe("recipe unavailable behaviour", () => {
  it("mission-health is unavailable with no audits", () => {
    const out = RECIPE_REGISTRY["mission-health"].derive({ audits: [] });
    expect(out.status).toBe("unavailable");
    expect(out.limitations.length).toBeGreaterThan(0);
  });

  it("supervisor-decision is unavailable with no audits", () => {
    const out = RECIPE_REGISTRY["supervisor-decision"].derive({ audits: [] });
    expect(out.status).toBe("unavailable");
  });

  it("replay-clock is unavailable with no events", () => {
    const out = RECIPE_REGISTRY["replay-clock"].derive({ events: [] });
    expect(out.status).toBe("unavailable");
  });

  it("event-stream is unavailable with no events", () => {
    const out = RECIPE_REGISTRY["event-stream"].derive({ events: [] });
    expect(out.status).toBe("unavailable");
  });

  it("velocity-command is unavailable with no plan", () => {
    const out = RECIPE_REGISTRY["velocity-command"].derive({});
    expect(out.status).toBe("unavailable");
    // Even when unavailable, the recipe states /cmd_vel is forbidden.
    expect(out.fields.forbidden_topic).toBe("/cmd_vel");
  });

  it("topic-availability is unavailable with no spatial artefact", () => {
    const out = RECIPE_REGISTRY["topic-availability"].derive({ spatial: null });
    expect(out.status).toBe("unavailable");
  });

  it("evidence-integrity is unavailable with no registry records", () => {
    const out = RECIPE_REGISTRY["evidence-integrity"].derive({ registry: [] });
    expect(out.status).toBe("unavailable");
  });
});

describe("recipe ok behaviour", () => {
  it("velocity-command emits bounded waypoint counts from the plan", () => {
    const out = RECIPE_REGISTRY["velocity-command"].derive({
      audit: { ...FIX_AUDIT, plan: FIX_PLAN },
    });
    expect(out.status).toBe("ok");
    expect(out.fields.waypoints).toBe(FIX_PLAN.waypoints.length);
    expect(out.fields.forbidden_topic).toBe("/cmd_vel");
  });

  it("replay-clock surfaces start/end timestamps verbatim", () => {
    const out = RECIPE_REGISTRY["replay-clock"].derive({
      events: [FIX_EVENT_INFO, { ...FIX_EVENT_INFO, event_id: "x", event_time_ns: 1000 }],
    });
    expect(out.status).toBe("ok");
    expect(out.fields.start_ns).toBe(0);
    expect(out.fields.end_ns).toBe(1000);
  });

  it("topic-availability preserves derivation_source verbatim", () => {
    const out = RECIPE_REGISTRY["topic-availability"].derive({
      spatial: FIX_SPATIAL_ARTIFACT,
    });
    expect(out.fields.derivation_source).toBe(
      FIX_SPATIAL_ARTIFACT.derivation_source,
    );
  });

  it("evidence-integrity preserves bag_backed counts verbatim", () => {
    const out = RECIPE_REGISTRY["evidence-integrity"].derive({
      registry: [FIX_REGISTRY_RECORD],
    });
    expect(out.fields.bag_backed).toBe(0);
    expect(out.fields.total).toBe(1);
  });
});

describe("recipes never throw", () => {
  it("every recipe handles an empty input", () => {
    for (const id of RECIPE_IDS) {
      const r = RECIPE_REGISTRY[id];
      // Should not throw.
      expect(() => r.derive({})).not.toThrow();
    }
  });
});
