/**
 * Phase 20B snapshot parser.
 *
 * Accepts a JSON string and returns the parsed snapshot plus a list
 * of validation issues. The parser NEVER throws on malformed input
 * — bad input surfaces as ``ok=false`` with a documented issue.
 */

import type { WorkspaceSnapshotV1 } from "./models";
import {
  validateWorkspaceSnapshot,
  type ValidationIssue,
} from "./validateWorkspaceSnapshot";

export interface ParseResult {
  ok: boolean;
  issues: ValidationIssue[];
  snapshot: WorkspaceSnapshotV1 | null;
}

export function parseWorkspaceSnapshot(input: string): ParseResult {
  let parsed: unknown;
  try {
    parsed = JSON.parse(input);
  } catch (err) {
    return {
      ok: false,
      issues: [
        {
          field: "$",
          message: `not valid JSON: ${(err as Error).message}`,
        },
      ],
      snapshot: null,
    };
  }
  return validateWorkspaceSnapshot(parsed);
}
