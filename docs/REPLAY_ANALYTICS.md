# Replay Analytics

This document describes the Phase 8 replay analytics layer. The
platform is **not safety-certified**; the analytics layer produces
engineering reliability material derived from existing artifacts.

## 1. Architectural principle

Analytics are **downstream of evidence**. The layer reads the
Phase-6 incident bundle and the Phase-7 replay-review bundle for
each incident and derives:

* coverage metrics (six deterministic ratios);
* a 0-100 quality score with explicit band caps;
* gaps and recommendations;
* per-incident review-completion audit;
* cross-incident trends + comparisons;
* a filterable analytics index.

The layer is **read-only**. It never mutates source artifacts and
never opens a bag file.

## 2. Pipeline

```
loader -> coverage -> scoring -> review_audit -> recommendations
                                                        |
                                                        v
                                          per-incident analytics report
                                                        |
                                                        v
                                  trends + comparison + index + reporter
```

Modules under `backend/app/replay_analytics/`:

| Module | Responsibility |
| --- | --- |
| `models.py` | typed dataclasses + controlled enums |
| `loader.py` | defensive incident-bundle loader (warnings, never exceptions) |
| `coverage.py` | six deterministic coverage metrics |
| `scoring.py` | 0..100 score with band caps; static-only/missing-bag/contradictions enforce the floor |
| `review_audit.py` | explicit-acknowledgement-only completion audit |
| `recommendations.py` | gap-to-recommendation mapping with citations |
| `trends.py` | distribution + top-N counters |
| `comparison.py` | extends Phase 6 comparator with replay-quality columns |
| `reporting.py` | aggregate Markdown + JSON renderers |
| `index.py` | filterable analytics index |

## 3. Coverage metrics

Each metric is one of `available=True, value=<float in [0, 100]>`
or `available=False, value=None`.

| Metric | Source | Notes |
| --- | --- | --- |
| `expected_topics_present_pct` | replay-review-manifest.json | unavailable when no bag inventory |
| `marker_alignment_pct` | replay-markers.json | unavailable when no markers |
| `timeline_alignment_pct` | incident-report.json timeline | fraction of entries with `sim_time_ns` |
| `replay_validation_pass_rate` | replay-review-report.json | unavailable when no validation results |
| `evidence_completeness_pct` | incident-report.json `evidence_status` | mapping table |
| `review_artifact_completeness_pct` | bundle dir | fraction of canonical files present |

## 4. Quality score bands

Score bands match `docs/REPLAY_QUALITY_SCORING.md`:

| Band | Meaning |
| --- | --- |
| 90-100 | bag-backed, aligned markers, complete evidence, validated replay, no contradictions |
| 70-89 | partial replay gaps, some missing inventory, acceptable evidence |
| 40-69 | sparse replay artifacts, missing markers, partial reports |
| 0-39 | static-only, missing bags, incomplete reports, contradictions |

The cap floor is enforced explicitly:

* `bag_status=ready` -> max 100
* `bag_status=partial` -> max 89
* `bag_status=missing_bag` -> max 59
* `bag_status=static_only` -> max 39
* `bag_status=not_executed | failed` -> max 39
* contradictions present -> max 39

Static-only and missing-bag incidents **never** receive an
artificially high score.

## 5. Review completion audit

Operator review completion is recognised **only** via an explicit
`review-audit.json` artifact. The audit module never infers
completion from any other artifact (no "the report exists, therefore
it was reviewed" shortcut). See
[docs/REPLAY_REVIEW_AUDIT.md](REPLAY_REVIEW_AUDIT.md) for the
schema.

## 6. CLIs

| Tool | Role |
| --- | --- |
| `rover_ws/tools/analyze_replay_coverage.py` | Per-incident analytics. |
| `rover_ws/tools/compare_replay_reviews.py` | Cross-incident comparison. |
| `rover_ws/tools/generate_replay_analytics.py` | Aggregate report + trends + gap analysis + index. |
| `rover_ws/tools/audit_replay_reviews.py` | Operator review-completion audit. |

## 7. Outputs

Per incident (`incidents/<incident_id>/`):

* `replay-analytics.md` / `.json`
* `replay-coverage.json`
* `replay-quality-score.json`
* `replay-gaps.json`
* `replay-recommendations.json`
* `review-audit.md` / `.json`

Cross-incident (`incidents/analytics/`):

* `replay-analytics-report.md` / `.json`
* `replay-quality-index.json`
* `replay-gap-analysis.md`
* `trends/replay-trends.md` / `.json`
* `comparisons/<comparison_id>.md` / `.json`
* `index.json`

Plus the canonical doc index at `docs/REPLAY_ANALYTICS_INDEX.md`.

## 8. CI

`.github/workflows/replay-analytics-review.yml` runs the full
analytics pipeline on every push touching incidents/ or the Phase-8
modules. The job is github-hosted by default and self-hosted only
when explicitly dispatched. The analytics layer never opens a bag
file, so github-hosted runs produce honest results (the bundles
simply have no bag inventory to inspect on CI).

## 9. Honesty rules

- Static-only and missing-bag incidents stay below their respective
  caps (39 / 59).
- Unavailable metrics never inflate the score; the weighted average
  is computed only over the metrics actually available, and the
  unavailable-metric penalty caps the score by lost weight.
- Contradictions force the score to <= 39.
- Operator review completion requires an explicit acknowledgement.
- Trend tables are deterministic counters; "most common" tables
  never claim statistical significance.
- Every report carries the verbatim certification disclaimer.

## 10. Phase 9 integration

The Phase 9 reliability-impact layer
(`backend/app/reliability_impact/`) consumes the analytics outputs
produced by this layer (`replay-quality-index.json` +
`replay-analytics-report.json`) and compares them against the
pinned baseline under `reliability-baselines/`. Score drops,
contradiction increases, and replay honesty violations become
gateable CI signals — see
[docs/RELIABILITY_IMPACT_ANALYSIS.md](RELIABILITY_IMPACT_ANALYSIS.md)
and [docs/CI_RELIABILITY_GATE.md](CI_RELIABILITY_GATE.md).

## 11. Phase 13 live-runtime input

When a Phase 13 live capture lands a bag-backed bundle in
`evidence/runtime/<run_id>/`, the
`process_live_runtime_evidence.py` orchestrator drives the same
analytics pipeline as a fixture-backed run. The honesty rules
remain unchanged: `static_only` and `missing_bag` flags propagate
verbatim, and `not_executed` runs are reported, never silently
upgraded. See
[docs/LIVE_RUNTIME_EVIDENCE_PIPELINE.md](LIVE_RUNTIME_EVIDENCE_PIPELINE.md).

## 12. Related documents

- [docs/REPLAY_QUALITY_SCORING.md](REPLAY_QUALITY_SCORING.md)
- [docs/REPLAY_REVIEW_AUDIT.md](REPLAY_REVIEW_AUDIT.md)
- [docs/REPLAY_GAP_ANALYSIS.md](REPLAY_GAP_ANALYSIS.md)
- [docs/REPLAY_REVIEW_RUNBOOK.md](REPLAY_REVIEW_RUNBOOK.md)
- [docs/INCIDENT_RECONSTRUCTION.md](INCIDENT_RECONSTRUCTION.md)
- [docs/RELIABILITY_IMPACT_ANALYSIS.md](RELIABILITY_IMPACT_ANALYSIS.md)
- [docs/CI_RELIABILITY_GATE.md](CI_RELIABILITY_GATE.md)
- [docs/VERIFICATION_STRATEGY.md](VERIFICATION_STRATEGY.md)
- [docs/REPLAY_ANALYTICS_INDEX.md](REPLAY_ANALYTICS_INDEX.md) — generated index.

## Phase 16 rehearsal analytics

The Phase 16 mission rehearsal pipeline produces a per-rehearsal
analytics artifact under `mission-rehearsals/audits/<id>/analytics.json`.
The artifact records `approved_count`, `rejected_count`, `aborted_count`,
`completed_count`, `supervisor_rejection_count`,
`validator_rejection_count`, and `deterministic_replay_stable`. The
artifacts are simulation-only — `bag_backed=False` is hardcoded for
every rehearsal replay bundle. See
`docs/REHEARSAL_REPLAY_INTEGRATION.md` for the schema and the
origin-labelling rule that keeps simulated counts from silently
mixing with bag-backed counts.
