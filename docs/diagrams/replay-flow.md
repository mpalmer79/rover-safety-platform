# Replay Flow

The platform is **not safety-certified**. This diagram shows the
event recording → replay → reconstruction loop.

```mermaid
sequenceDiagram
    autonumber
    participant Engine as Deterministic engine /<br/>ROS 2 runtime
    participant Sup as Safety supervisor
    participant Rec as Event recorder
    participant Disk as runs/&lt;id&gt;/<br/>events.jsonl + manifest.json
    participant Bag as ROS 2 bag (optional)
    participant Verifier as Replay verifier /<br/>tools/verify_replay_integrity.py
    participant Reconstructor as Incident reconstructor
    participant Review as Replay review
    participant Exporter as Reviewer export

    Engine->>Sup: requested commands, sensor inputs
    Sup-->>Rec: safety-state transition events
    Sup-->>Rec: command-authorisation events
    Engine-->>Rec: mission, fault, world events
    Rec->>Disk: append events.jsonl
    Engine->>Disk: write manifest.json
    Engine->>Bag: (Jazzy host only) record bag

    Note over Disk,Bag: Replay sources: events.jsonl alone,<br/>or events.jsonl + bag

    Verifier->>Disk: read events + manifest
    Verifier-->>Disk: write replay-integrity.json

    Reconstructor->>Disk: read events + manifest
    Reconstructor->>Bag: (if available) read bag
    Reconstructor-->>Disk: write incident-report.json

    Review->>Disk: read incident-report.json
    Review->>Bag: (if available) read bag
    Review-->>Disk: write replay-review-report.json<br/>(static_only / missing_bag preserved)

    Exporter->>Disk: read replay-review-report.json
    Exporter-->>Disk: write reviewer-export/csv/replay_quality.csv<br/>(origin flags propagated)
```

## Properties enforced by the replay layer

| Property | Where it lives |
| --- | --- |
| Events ordered, schema-validated | `backend/app/replay/recorder.py` + `tools/verify_replay_integrity.py` |
| `run_id` and `scenario_id` consistent | `tools/verify_replay_integrity.py` |
| Required markers present (e.g. recovery completion) | scenario expectations in `backend/app/verification/scenario_verifier.py` |
| Safety + mission transitions reconstructable from events | `backend/app/incident_analysis/` reconstructor |
| `static_only` / `missing_bag` flags preserved end-to-end | `backend/app/replay_review/` → `backend/app/reviewer_exports/exporters.py` |

## What "static_only" and "missing_bag" mean

- **`static_only`** — the replay review ran against `events.jsonl`
  alone; no ROS 2 bag was available. The review still grades the
  evidence, but the result is honestly labelled.
- **`missing_bag`** — a bag was *expected* but not present. The
  review records the gap rather than silently treating it as
  static-only.

Both flags propagate verbatim into:

- `incidents/<id>/replay-review-report.json`
- `incidents/analytics/replay-analytics-report.json`
- `reviewer-export/csv/replay_quality.csv`

Reviewers should treat any row with `static_only=true` or
`missing_bag=true` as evidence-limited, never as live-runtime.

## Related documents

- [`docs/REPLAY_SYSTEM.md`](../REPLAY_SYSTEM.md)
- [`docs/REPLAY_REVIEW_RUNBOOK.md`](../REPLAY_REVIEW_RUNBOOK.md)
- [`docs/REPLAY_QUALITY_SCORING.md`](../REPLAY_QUALITY_SCORING.md)
- [`docs/REPLAY_GAP_ANALYSIS.md`](../REPLAY_GAP_ANALYSIS.md)
- [`docs/FOXGLOVE_REPLAY_WORKFLOW.md`](../FOXGLOVE_REPLAY_WORKFLOW.md)
- [`docs/diagrams/evidence-flow.md`](evidence-flow.md)
