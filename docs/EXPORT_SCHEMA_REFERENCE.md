# Reviewer Export Schema Reference

Every reviewer-export table ships a JSON Schema under
`reviewer-export/schemas/`. This document is the human-readable
companion: it lists each table's fields, type, and notes about
what the values mean. The platform is **not safety-certified**;
this reference is engineering review material.

## Conventions

* Every field is required by name. Nullability is encoded via
  `type: ["string", "null"]` etc.
* Booleans are emitted as JSON booleans in JSONL and as the strings
  `true` / `false` in CSV.
* Numeric fields use a fixed 4-decimal precision when serialised to
  CSV; trailing zeros are trimmed.
* Enums are explicit; reviewers can grep schemas for the exact
  allowed values.

## Tables

### `programme_health`

| Field | Type | Notes |
| --- | --- | --- |
| `generated_at` | string | UTC ISO-8601 timestamp from the underlying programme review. |
| `programme_health` | enum | One of `strong`, `acceptable`, `weak`, `concerning`, `critical`. |
| `discipline` | enum | One of the six discipline categories (`evidence`, `replay`, `ci`, `traceability`, `runtime_qualification`, `review_completion`) or `unknown`. |
| `discipline_rating` | enum | One of `strong`, `acceptable`, `weak`, `concerning`, `unknown`. |
| `reason` | string | The reason recorded by the discipline check. |
| `triggering_artifact` | nullable string | Path to the artefact that triggered the rating, if any. |
| `evidence_origin` | nullable string | Carried through from the source where applicable. |
| `known_limitation` | nullable string | First entry from the upstream known-limitations list. |

### `trend_series`

| Field | Type | Notes |
| --- | --- | --- |
| `metric_name` | string | Series label (e.g. `analytics_average_score`). |
| `window` | enum | `full`, `rolling_3`, or `rolling_5`. |
| `trend_category` | enum | One of `improving`, `stable`, `degrading`, `volatile`, `insufficient_history`. |
| `latest_value` | nullable number/string | Last available value (4-decimal precision in CSV). |
| `baseline_value` | nullable number/string | First available value. |
| `delta` | nullable number/string | `latest_value − baseline_value` when both are available. |
| `sample_count` | integer | Number of available samples (≥ 0). |
| `history_status` | nullable string | `available` or `insufficient_history`. |
| `evidence_origin_mix` | nullable string | `static_only_only` / `bag_backed_only` / `mixed_origin` / `unavailable`. |

### `drift_findings`

| Field | Type | Notes |
| --- | --- | --- |
| `finding_id` | string | Stable id (`drift-NNNN`). |
| `drift_type` | string | The drift detector label (e.g. `analytics_score_regression`). |
| `severity` | enum | `informational` / `warning` / `regression` / `critical_regression`. |
| `description` | string | The detail string from the upstream finding. |
| `affected_metric` | nullable string | Best-effort metric extracted from the label. |
| `current_value` | nullable | Reserved for future use; currently null. |
| `baseline_value` | nullable | Reserved for future use; currently null. |
| `triggering_artifact` | nullable string | Joined evidence paths. |
| `evidence_origin` | nullable string | Carried through where available. |

### `subsystem_risk`

| Field | Type | Notes |
| --- | --- | --- |
| `subsystem` | string | Subsystem identifier. |
| `risk_frequency` | integer | Number of bundles that named this subsystem. |
| `highest_risk` | enum | Highest severity level recorded against the subsystem. |
| `warning_count` | integer | `moderate` severity count. |
| `failure_count` | integer | `high` severity count. |
| `critical_count` | integer | `critical` severity count. |
| `representative_artifacts` | string | Up to three artefact paths (`;`-joined). |
| `causality_claimed` | boolean (`false` only) | **Honesty constant**: the export never claims causality. |

### `gate_history`

| Field | Type | Notes |
| --- | --- | --- |
| `gate_status` | enum | `passed` / `warning` / `failed` / `not_executed` / `unknown`. |
| `count` | integer | Number of bundles ending in this gate status. |
| `latest_status` | enum | The most recent gate status across history. |
| `volatility` | enum | `steady` / `oscillating` / `regressing` / `improving` / `unknown`. |
| `last_transition` | nullable string | E.g. `passed -> warning`. |
| `history_status` | nullable string | `available` or `insufficient_history`. |

### `replay_quality`

| Field | Type | Notes |
| --- | --- | --- |
| `incident_id` | string | Incident identifier. |
| `score` | nullable integer | 0..100 quality score from Phase 8. |
| `coverage_status` | enum | One of the documented coverage labels. |
| `confidence` | enum | `high` / `moderate` / `low` / `unknown`. |
| `bag_status` | enum | `ready` / `partial` / `missing_bag` / `static_only` / `not_executed` / `failed` / `passed` / `unknown`. |
| `evidence_status` | nullable string | Phase-6 evidence status. |
| `review_completion_status` | nullable string | `not_started` / `partial` / `completed` / `inconclusive`. |
| `evidence_origin` | enum | `scenario-evidence` / `runtime-evidence` / `live-runtime` / `bag-backed` / `static-source` / `static-workspace` / `unknown`. |
| `static_only` | boolean | `true` iff `bag_status == static_only`. |
| `missing_bag` | boolean | `true` iff `bag_status == missing_bag`. |

### `incident_index`

| Field | Type | Notes |
| --- | --- | --- |
| `incident_id` | string | Incident identifier. |
| `run_id` | nullable string | Underlying run id, when known. |
| `scenario_id` | nullable string | Scenario id, when known. |
| `severity` | enum | `informational` / `low` / `moderate` / `high` / `critical` / `unknown`. |
| `outcome` | enum | `controlled_degradation` / `safe_stop_success` / `estop_latched` / `mission_aborted` / `recovery_success` / `recovery_failed` / `inconclusive` / `unknown`. |
| `evidence_status` | nullable string | Phase-6 evidence status. |
| `first_fault` | nullable string | First-fault label (free text). |
| `terminal_safety_state` | nullable string | E.g. `SAFE_STOP`, `E_STOP_LATCHED`. |
| `replay_integrity_status` | nullable string | `passed` / `failed` / `-`. |
| `report_path` | nullable string | Path to the incident bundle's `incident-report.json`. |

### `requirement_coverage`

| Field | Type | Notes |
| --- | --- | --- |
| `requirement_id` | string | E.g. `REQ-SAFE-001`. |
| `requirement_kind` | string | `safety`, `runtime`, `replay`, ... |
| `title` | nullable string | Human-readable title. |
| `status` | nullable string | `passed` / `partial` / `not_executed`. |
| `mapped_tests` | integer | Number of test refs declared on the requirement. |
| `mapped_artifacts` | integer | Number of evidence artefacts the matrix recorded. |
| `coverage_status` | enum | `covered` / `tests_only` / `evidence_only` / `unmapped`. |

## Honesty rules surfaced via the schemas

* `causality_claimed` is constrained to `false` via JSON Schema's
  `const: false`.
* `programme_health`, `discipline`, `severity`, `coverage_status`,
  `evidence_origin`, `bag_status`, etc. are constrained to the
  documented enum sets so reviewers can spot drift quickly.
* Numeric fields permit `null` so missing data never becomes a
  spurious zero.

## Related documents

- [docs/REVIEWER_EXPORTS.md](REVIEWER_EXPORTS.md)
- [docs/REVIEWER_NOTEBOOK_GUIDE.md](REVIEWER_NOTEBOOK_GUIDE.md)
- [docs/PROGRAMME_REVIEW.md](PROGRAMME_REVIEW.md)
