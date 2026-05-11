# Rehearsal Replay + Analytics Integration

The platform is **not safety-certified.** This page documents how
Phase 16 mission rehearsals (simulation-only) plug into the
existing replay-review and replay-analytics layers without
claiming bag-backed evidence.

## 1. Replay bundle

```jsonc
{
  "mission_id": "<id>",
  "evidence_status": "simulated",      // simulated | static_only | not_evaluated
  "bag_backed": false,                  // ALWAYS false for Phase 16
  "review_status": "passed" | "partial" | "rejected" | "not_evaluated",
  "deterministic_hash": "...",          // hash over plan + runtime + markers
  "replay_markers": [
    {
      "marker_id": "<event_id>",
      "type": "mission" | "motion" | "safety" | "supervisor",
      "subtype": "...",
      "time_ns": 0,                     // sequence-derived, not wall-clock
      "deterministic_hash": "...",
      "description": "..."
    }
  ],
  "rendered_markdown": "...",
  "notes": ["..."]
}
```

The bundle is built by `rehearsal_replay_bridge.build_replay_bundle`.
Bag-backed evidence is **never** claimed: there is no real bag.

## 2. Analytics result

```jsonc
{
  "mission_id": "<id>",
  "rehearsal_count": 1,
  "approved_count": 1,
  "rejected_count": 0,
  "aborted_count": 0,
  "completed_count": 1,
  "supervisor_rejection_count": 0,
  "validator_rejection_count": 0,
  "deterministic_replay_stable": true,
  "notes": ["..."]
}
```

The result is per-rehearsal. Programme review aggregates many
rehearsals from disk; aggregation is intentionally out of scope for
the rehearsal layer itself.

Counters are mutually consistent:

* `completed_count` requires `approved_count` ≥ 1 and zero
  validator / supervisor rejections;
* `rejected_count` includes any final-status rejection regardless
  of whether the cause was validator or supervisor;
* `supervisor_rejection_count` and `validator_rejection_count` are
  independent flags;
* `deterministic_replay_stable` is `true` whenever the runtime
  emitted a non-empty deterministic hash.

## 3. Replay-review consistency

The rendered Markdown begins with the verbatim Phase 16 disclaimer.
Markers include only events from the four operator-relevant event
families (`mission`, `motion`, `safety`, `supervisor`). The
`validation`, `replay`, `analytics`, and `audit` event families are
captured by the audit bundle but not lifted into the replay
markers.

## 4. Honesty rules

* The replay bundle records `evidence_status='simulated'` and
  `bag_backed=False`. A run that ever flips either of these must
  fail an honesty test.
* Analytics produces deterministic integer counts only — no
  probabilities, no AI-derived metrics.
* The `deterministic_replay_stable` flag is set by the rehearsal
  runtime; downstream tooling treats it as a binary signal, not a
  confidence score.
* Programme review consumes Phase 16 analytics through the same
  filesystem layout as Phase 8 analytics, but the artefacts are
  labelled `simulated` so trends do not silently mix bag-backed
  data with rehearsal data.

## 5. Honest aggregation

Aggregating Phase 16 analytics across many rehearsals is allowed.
Aggregating Phase 16 analytics *with* live bag-backed analytics is
not allowed without explicit origin labelling — programme review
already enforces an `origin_mix_label` for mixed samples.
