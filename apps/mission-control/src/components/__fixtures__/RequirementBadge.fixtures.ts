/**
 * Catalog fixtures for RequirementBadge.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { RequirementBadge } from "@/components/RequirementBadge";


type Props = ComponentProps<typeof RequirementBadge>;

export const STATES: Record<string, Props> = {
  passed: ({ reqId: "REQ-SAFE-001", status: "passed" }) as Props,
  not_executed: ({ reqId: "REQ-LIVE-001", status: "not_executed" }) as Props,
  failed: ({ reqId: "REQ-SAFE-002", status: "failed" }) as Props,
};
