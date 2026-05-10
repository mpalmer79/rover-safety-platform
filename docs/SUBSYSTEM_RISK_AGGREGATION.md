# Subsystem Risk Aggregation

Phase 10's subsystem-risk aggregator counts how often each
subsystem appeared in the loaded history, tallies the severity
distribution of recorded risks, and ranks the rows. The platform
is **not safety-certified**; this aggregation is engineering
analytics material.

## 1. Inputs

Each reliability-impact bundle contributes:

* a list of impacted subsystems (from `subsystem_impacts`);
* a list of `assessment.risks` entries with a `level` ∈
  `{none, low, moderate, high, critical}`;
* a gate decision (`passed` / `warning` / `failed` / `not_executed`).

## 2. Per-subsystem counts

| Field | What it counts |
| --- | --- |
| `frequency` | Number of bundles that listed the subsystem. |
| `severity_distribution` | Severity-keyed counter of risk levels recorded against the subsystem. |
| `repeat_regression_count` | Risks classified as `high` or `critical`. |
| `gate_failure_count` | Bundles whose gate ended `failed`. |
| `unresolved_warning_count` | Risks of `moderate` or higher. |
| `representative_artifacts` | Up to three source paths for the subsystem. |

## 3. Ranking

Rows are ordered:

1. highest `repeat_regression_count`;
2. then highest weighted severity score
   (`critical=10`, `high=5`, `moderate=2`, `low=1`, `none=0`);
3. then highest `frequency`;
4. then subsystem name (alphabetical).

## 4. Honesty rules

* The aggregator never claims causation. A row says "this
  subsystem appeared in N bundles with these severities" — not
  "this subsystem caused those failures."
* No subsystem is ever promoted or demoted via heuristic. Every
  field is a deterministic count.
* `representative_artifacts` is bounded by the actual paths.

## 5. Related documents

- [docs/PROGRAMME_REVIEW.md](PROGRAMME_REVIEW.md)
- [docs/RELIABILITY_IMPACT_ANALYSIS.md](RELIABILITY_IMPACT_ANALYSIS.md)
- [docs/SOURCE_TO_EVIDENCE_TRACEABILITY.md](SOURCE_TO_EVIDENCE_TRACEABILITY.md)
