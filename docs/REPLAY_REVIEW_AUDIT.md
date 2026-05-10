# Replay Review Audit

This document describes the operator-review-completion audit
produced by `backend/app/replay_analytics/review_audit.py`. The
platform is **not safety-certified**; the audit is engineering
analytics material.

## 1. Principle: never infer completion

The audit module recognises completion **only** via an explicit
`review-audit.json` artefact under `incidents/<incident_id>/`. If
the file is absent the audit reports `not_started`; the analytics
layer never promotes a missing acknowledgement to `completed`.

## 2. Schema

`incidents/<incident_id>/review-audit.json`:

```json
{
  "incident_id": "<id>",
  "operator": "<name or label>",
  "completed_steps": ["bag_status_reviewed", "..."],
  "status_override": "completed",
  "notes": "<free text>"
}
```

Fields:

* `incident_id` — must match the bundle. Free-form; the audit
  module does not cross-check it.
* `operator` — optional free text. Recommended.
* `completed_steps` — list of step ids. Only members of the
  canonical checklist (see below) are honoured; unknown ids are
  silently dropped (the audit ignores them rather than fabricating
  a custom step).
* `status_override` — optional. When present, must be one of
  `not_started` / `partial` / `completed` / `inconclusive`. The
  override wins over the inferred status.
* `notes` — optional free text.

## 3. Canonical checklist

The canonical step ids:

* `bag_status_reviewed`
* `missing_topics_reviewed`
* `markers_loaded`
* `safety_state_matches_report`
* `cmd_vel_arbitration_matches_audit`
* `replay_integrity_checked`
* `discrepancies_recorded_outside_bundle`

## 4. Inferred status

When `status_override` is absent the audit infers from
`completed_steps`:

* zero recognised steps → `not_started`
* every canonical step recognised → `completed`
* otherwise → `partial`

## 5. Inconclusive

Two paths produce `inconclusive`:

* the `review-audit.json` file is present but does not parse as a
  JSON object;
* `status_override` is present but is not one of the four
  recognised values.

## 6. CLI

```bash
python3 rover_ws/tools/audit_replay_reviews.py
# Audits every incident bundle under incidents/

python3 rover_ws/tools/audit_replay_reviews.py \
  --incident incidents/<incident_id>
# Audits a single bundle.
```

The CLI writes `review-audit.json` and `review-audit.md` into the
bundle directory. When no `review-audit.json` was supplied the
output mirrors the inferred `not_started` status — the file
materialised by the CLI is *the audit*, not the operator's
acknowledgement.

To record an actual operator acknowledgement, the operator must
hand-edit (or generate from another tool) the `review-audit.json`
file with `status_override="completed"` (or by listing every
canonical step).

## 7. Honesty rules

- Completion is recognised only from explicit metadata.
- Unknown step ids are dropped; the audit never fabricates
  completion based on bundle contents.
- `inconclusive` is preferred over `completed` when the metadata
  shape is unexpected.

## 8. Related documents

- [docs/REPLAY_ANALYTICS.md](REPLAY_ANALYTICS.md)
- [docs/REPLAY_QUALITY_SCORING.md](REPLAY_QUALITY_SCORING.md)
- [docs/REPLAY_REVIEW_RUNBOOK.md](REPLAY_REVIEW_RUNBOOK.md)
