# Replay Quality Scoring

This document describes the deterministic 0..100 replay quality
score produced by `backend/app/replay_analytics/scoring.py`. The
platform is **not safety-certified**; the score is engineering
analytics material.

## 1. Inputs

The score consumes the per-incident
:class:`ReplayCoverageReport` plus the loaded incident bundle.
Specifically:

* the six coverage metrics (each `available=True/False`, `value=float|None`);
* the Phase-7 bag status (`ready`, `partial`, `missing_bag`,
  `static_only`, `not_executed`, `failed`, `passed`);
* the contradiction count from the Phase-6 incident report;
* the missing-topic count from the Phase-7 manifest.

## 2. Output

A :class:`ReplayQualityScore` with:

* `score` — integer 0..100;
* `confidence` — `high` / `moderate` / `low`;
* `coverage_status` — mirror of the coverage report;
* `quality_summary` — human-readable summary;
* `blocking_gaps` — list of explicit gap labels.

## 3. Score bands

| Band | Meaning |
| --- | --- |
| 90-100 | bag-backed; markers exact; complete evidence; validated replay; no contradictions |
| 70-89  | partial replay gaps; some missing inventory; acceptable evidence quality |
| 40-69  | sparse replay artefacts; missing markers; partial reports |
| 0-39   | static-only; missing bags; incomplete reports; contradictions |

## 4. Algorithm

1. **Weighted average** of available metrics. The metric weights
   sum to 100:

   | Metric | Weight |
   | --- | --- |
   | `expected_topics_present_pct` | 25 |
   | `replay_validation_pass_rate` | 20 |
   | `evidence_completeness_pct` | 20 |
   | `marker_alignment_pct` | 15 |
   | `timeline_alignment_pct` | 10 |
   | `review_artifact_completeness_pct` | 10 |

   Unavailable metrics drop out of both numerator and denominator.

2. **Bag-status floor** caps the weighted average:

   | Bag status | Floor (max score) |
   | --- | --- |
   | `ready` / `passed` | 100 |
   | `partial` | 89 |
   | `missing_bag` | 59 |
   | `static_only` | 39 |
   | `not_executed` / `failed` | 39 |

3. **Unavailable-metric penalty.** For each unavailable metric, we
   cap the score by `100 - weight_lost`. This keeps the score from
   floating to 100 when only a subset of metrics is computable.

4. **Contradiction cap.** When the Phase-6 incident report lists
   any contradictions, the score is capped at 39 — the lowest
   band, regardless of any other signal.

5. **Confidence label**:

   | bag_status | unavailable metrics | confidence |
   | --- | --- | --- |
   | `static_only` / `missing_bag` | any | `low` |
   | `ready` / `partial` | any | `moderate` |
   | `ready` / `partial` | none | `high` |

## 5. Determinism

The same inputs always yield the same score. The
`test_scoring_is_deterministic` and
`test_coverage_metrics_are_deterministic` tests pin this contract.
Any change to the scoring algorithm forces a re-roll of the
canonical analytics artefacts in `incidents/analytics/`.

## 6. Honesty rules

- Static-only incidents cannot rise above 39.
- Missing-bag incidents cannot rise above 59.
- Contradictions cap the score at 39 even when bag chunks exist.
- Unavailable metrics never inflate the score.
- The function returns 0 + `coverage_status=missing` when no
  Phase-7 replay-review bundle exists.

## 7. Related documents

- [docs/REPLAY_ANALYTICS.md](REPLAY_ANALYTICS.md)
- [docs/REPLAY_GAP_ANALYSIS.md](REPLAY_GAP_ANALYSIS.md)
- [docs/REPLAY_REVIEW_AUDIT.md](REPLAY_REVIEW_AUDIT.md)
- [docs/REPLAY_REVIEW_RUNBOOK.md](REPLAY_REVIEW_RUNBOOK.md)
