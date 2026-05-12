/**
 * Phase 20 reviewer walkthrough script.
 *
 * Ten deterministic steps explain the platform end-to-end in 3-5
 * minutes. The script is consumed by the walkthrough overlay and
 * is rendered as plain JSX text — no copy is fabricated by an LLM
 * or generated at runtime.
 */

export type WalkthroughStepId =
  | "operator-request"
  | "proposal-generation"
  | "sanitizer-decision"
  | "compiler-result"
  | "validator-result"
  | "supervisor-decision"
  | "rehearsal-execution"
  | "replay-evidence"
  | "analytics-outcome"
  | "unresolved-limitations";

export interface WalkthroughStep {
  id: WalkthroughStepId;
  index: number;
  title: string;
  narrative: string;
  evidence: readonly string[];
  safety: string;
  outcome: string;
}

export const WALKTHROUGH_STEPS: readonly WalkthroughStep[] = [
  {
    id: "operator-request",
    index: 1,
    title: "Operator request",
    narrative:
      "A reviewer or operator names a mission request and a target ODD profile. The platform records the request id verbatim — it is the first deterministic identifier in the bundle.",
    evidence: [
      "rehearsal_audit.request",
      "mission_id, request_id, seed, operator, odd_profile_id",
    ],
    safety:
      "The request does not grant any execution authority. No /cmd_vel publication is implied.",
    outcome:
      "request_id is bound to the mission_id and the audit pipeline begins.",
  },
  {
    id: "proposal-generation",
    index: 2,
    title: "Proposal generation",
    narrative:
      "Either an LLM-candidate or a deterministic generator produces a proposed plan. Proposals never bypass the compiler; they are inputs only.",
    evidence: [
      "mission_proposals/<id>/proposal.json",
      "skill-llm-candidates/<run>/candidate.json",
    ],
    safety:
      "Proposals are advisory. The sanitizer + compiler downstream remain the only authority for emitting a plan.",
    outcome: "A candidate proposal is captured for review.",
  },
  {
    id: "sanitizer-decision",
    index: 3,
    title: "Sanitizer decision",
    narrative:
      "The sanitizer audits the proposal for forbidden topics, forbidden actions, and bounded-input violations.",
    evidence: ["sanitizer_audit.json", "validation_diagnostics"],
    safety:
      "Forbidden topics include /cmd_vel; the sanitizer rejects any proposal that targets it directly.",
    outcome:
      "Either a sanitized proposal is forwarded, or the audit terminates with a rejection.",
  },
  {
    id: "compiler-result",
    index: 4,
    title: "Compiler result",
    narrative:
      "The mission compiler converts the sanitized proposal into a deterministic mission plan with bounded waypoints and explicit speed / distance limits.",
    evidence: ["mission_plan.json", "deterministic_hash"],
    safety:
      "The plan never targets /cmd_vel directly. Bounded values are honoured by every downstream stage.",
    outcome: "A plan with a deterministic hash, or a compile-time rejection.",
  },
  {
    id: "validator-result",
    index: 5,
    title: "Validator result",
    narrative:
      "The validator replays the plan against the canonical ODD profile and emits diagnostics. Information, warnings, and rejections are preserved verbatim.",
    evidence: ["rehearsal_audit.validation_diagnostics"],
    safety: "Validator rejections halt the audit before supervisor review.",
    outcome:
      "A diagnostic set is attached to the audit. A rejection short-circuits to the supervisor.",
  },
  {
    id: "supervisor-decision",
    index: 6,
    title: "Supervisor decision",
    narrative:
      "The supervisor renders the only authority for mission approval. It can require human review, reject outright, or approve.",
    evidence: ["rehearsal_audit.decision"],
    safety:
      "The supervisor is the single safety authority and may revoke a plan even after validator approval.",
    outcome: "decision_status + safety_status are recorded verbatim.",
  },
  {
    id: "rehearsal-execution",
    index: 7,
    title: "Rehearsal execution",
    narrative:
      "Approved plans are executed inside the deterministic rehearsal runtime. Every transition is captured as a hashed event.",
    evidence: [
      "rehearsal_audit.runtime",
      "events (event_id, deterministic_hash)",
    ],
    safety:
      "The runtime is simulation-only; no physical robot is commanded.",
    outcome: "A timeline of hashed events is captured.",
  },
  {
    id: "replay-evidence",
    index: 8,
    title: "Replay evidence",
    narrative:
      "Replay artefacts attach an evidence_status (simulated, static_only, or not_evaluated) and a bag_backed boolean. The boolean is preserved verbatim.",
    evidence: [
      "replay_bundle.json",
      "spatial-replay artefact",
      "artifact registry record",
    ],
    safety:
      "If bag_backed is false, the UI never claims the run is bag-backed.",
    outcome: "A replay bundle is stamped onto the audit.",
  },
  {
    id: "analytics-outcome",
    index: 9,
    title: "Analytics outcome",
    narrative:
      "Analytics roll up rehearsal counters, deterministic-replay stability, and rejection ratios across runs.",
    evidence: ["rehearsal_analytics.json"],
    safety:
      "Analytics never imply live-runtime maturity beyond not_established.",
    outcome:
      "Counters + the deterministic_replay_stable flag are surfaced for review.",
  },
  {
    id: "unresolved-limitations",
    index: 10,
    title: "Unresolved limitations",
    narrative:
      "Every audit carries a verbatim limitations list. The walkthrough renders them last so the reviewer leaves with an honest picture of what is NOT covered.",
    evidence: [
      "rehearsal_audit.disclaimer",
      "live_runtime_maturity.known_limitations",
    ],
    safety:
      "The platform remains simulation-only and is not safety-certified. No live-runtime authority is implied.",
    outcome:
      "Reviewer leaves with the unresolved-limitations list intact.",
  },
];

export const WALKTHROUGH_STEP_COUNT = WALKTHROUGH_STEPS.length;
