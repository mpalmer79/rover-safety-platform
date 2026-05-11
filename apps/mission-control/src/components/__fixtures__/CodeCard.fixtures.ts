/**
 * Catalog fixtures for CodeCard.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { CodeCard } from "@/components/CodeCard";


type Props = ComponentProps<typeof CodeCard>;

export const STATES: Record<string, Props> = {
  rejected: ({
              skill: {
                skill_id: "s",
                skill_type: "move_forward_distance",
                language: "python_ros2",
                title: "Move forward 0.5m",
                subtitle: "Sample candidate",
                risk_band: "guarded",
                safety_status: "needs_review",
                generated_at_utc: "",
                code: "publisher.publish(Twist())",
                code_card: { safety_badges: [], animation_steps: [] },
              },
            }) as Props,
};
