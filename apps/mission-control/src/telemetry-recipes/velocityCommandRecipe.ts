import type { RecipeOutput, TelemetryRecipe } from "./models";

export const VELOCITY_COMMAND_RECIPE: TelemetryRecipe = {
  recipeId: "velocity-command",
  requires: ["mission_plan"],
  optional: [],
  compatibility: ["VelocityCommandPanel"],
  limitationNotes: [
    "Bounded velocity values come from the compiled mission plan.",
    "/cmd_vel is always forbidden; /cmd_vel_requested is the only allowed publisher.",
  ],
  derive(input): RecipeOutput {
    const plan = input.audit?.plan ?? null;
    if (!plan) {
      return {
        recipeId: "velocity-command",
        status: "unavailable",
        limitations: [
          "No mission plan available — rejected mission or audit not loaded.",
        ],
        sources: ["mission_plan"],
        fields: {
          forbidden_topic: "/cmd_vel",
          allowed_topic: "/cmd_vel_requested",
        },
      };
    }
    const maxSpeed = plan.waypoints.reduce(
      (m, w) => Math.max(m, w.bounded_speed_mps),
      0,
    );
    const maxDist = plan.waypoints.reduce(
      (m, w) => Math.max(m, w.bounded_distance_m),
      0,
    );
    return {
      recipeId: "velocity-command",
      status: "ok",
      limitations: [],
      sources: ["mission_plan"],
      fields: {
        waypoints: plan.waypoints.length,
        max_bounded_speed_mps: maxSpeed,
        max_bounded_distance_m: maxDist,
        forbidden_topic: "/cmd_vel",
        allowed_topic: "/cmd_vel_requested",
      },
    };
  },
};
