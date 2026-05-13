import type { RecipeOutput, TelemetryRecipe } from "./models";

export const TOPIC_AVAILABILITY_RECIPE: TelemetryRecipe = {
  recipeId: "topic-availability",
  requires: ["spatial_replay"],
  optional: [],
  compatibility: ["TopicAvailabilityPanel"],
  limitationNotes: [
    "Topic counts come from the spatial-replay artifact only.",
  ],
  derive(input): RecipeOutput {
    const a = input.spatial ?? null;
    if (!a) {
      return {
        recipeId: "topic-availability",
        status: "unavailable",
        limitations: ["No spatial-replay artifact for this mission."],
        sources: ["spatial_replay"],
        fields: {},
      };
    }
    return {
      recipeId: "topic-availability",
      status: a.missing_topics.length === 0 ? "ok" : "partial",
      limitations: [],
      sources: ["spatial_replay"],
      fields: {
        present_count: a.topic_sources.length,
        missing_count: a.missing_topics.length,
        derivation_source: a.derivation_source,
      },
    };
  },
};
