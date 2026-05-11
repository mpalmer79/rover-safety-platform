# Programme Review

Phase 10 introduces the longitudinal governance layer. The platform
is **not safety-certified**; this document describes engineering
reliability governance.

## 1. Scope

The programme-review layer aggregates artefacts produced by every
prior phase:

| Phase | Artefact consumed |
| --- | --- |
| 3 | `verification/traceability.json`, `docs/TRACEABILITY_MATRIX.md` |
| 4 | `evidence/runtime/<id>/runtime-validation.json` |
| 5 | `evidence/runtime/<id>/qualification-summary.json` |
| 6 | `incidents/<id>/incident-report.json` |
| 7 | `incidents/<id>/replay-review-report.json` |
| 8 | `incidents/analytics/replay-analytics-report.json` |
| 9 | `reliability-impact/.../impact-report.json` |

It produces:

| Output | Purpose |
| --- | --- |
| `programme-review.json` / `.md` | full report |
| `programme-health.json` / `.md` | governance health rollup |
| `trend-report.json` / `.md` | deterministic trends |
| `drift-report.json` / `.md` | drift findings |
| `subsystem-risk-report.json` / `.md` | per-subsystem aggregate |
| `coverage-evolution.json` / `.md` | replay-coverage timeline |
| `gate-history.json` / `.md` | CI gate history |
| `freshness-report.json` / `.md` | evidence freshness |
| `governance-dashboard.json` | compact dashboard payload |
| `index.json` | summary header |

## 2. Architectural principle

The layer is **read-only** with respect to every upstream artefact.
It inspects, classifies, aggregates, and reports.

* No causal claims.
* No fabricated history.
* No auto-baseline updates.
* No wall-clock dependencies inside the library (tests are
  deterministic; CI passes the reference time explicitly).

## 3. Status vocabularies

The layer mixes prior-phase enums with three of its own:

| Vocabulary | Values |
| --- | --- |
| Trends | `improving`, `stable`, `degrading`, `volatile`, `insufficient_history` |
| Drift severity | `informational`, `warning`, `regression`, `critical_regression` |
| Governance health | `strong`, `acceptable`, `weak`, `concerning`, `critical` |
| Discipline rating | `strong`, `acceptable`, `weak`, `concerning`, `unknown` |
| Freshness | `fresh`, `stale`, `unknown` |
| Gate volatility | `steady`, `oscillating`, `regressing`, `improving`, `unknown` |

Insufficient history is **always** a label, never a regression.

## 4. Modules

Under `backend/app/programme_review/`:

| Module | Role |
| --- | --- |
| `models.py` | Typed dataclasses + enums. |
| `history_loader.py` | Defensive multi-source loader; malformed JSON becomes a warning. |
| `trend_analysis.py` | Deterministic trend classifier with rolling-3 / rolling-5 windows. |
| `drift_detection.py` | Documented drift rules. |
| `governance_health.py` | Six-discipline rollup. |
| `freshness.py` | Reference-time-driven freshness check (no `datetime.now()`). |
| `subsystem_risk.py` | Per-subsystem severity aggregation. |
| `coverage_evolution.py` | Origin-preserving coverage history. |
| `gate_history.py` | CI gate outcome sequence + volatility. |
| `aggregation.py` | Composes :class:`ProgrammeReview`. |
| `reporting.py` | Markdown + JSON renderers + bundle writer. |
| `dashboard.py` | Compact dashboard payload. |

## 5. CLIs

| Tool | Purpose |
| --- | --- |
| `rover_ws/tools/generate_programme_review.py` | Full programme review bundle. |
| `rover_ws/tools/analyze_reliability_trends.py` | Trend report only. |
| `rover_ws/tools/detect_reliability_drift.py` | Drift report only. |
| `rover_ws/tools/review_governance_health.py` | Governance health only. |
| `rover_ws/tools/review_evidence_freshness.py` | Freshness only. |

All CLIs accept `--reference-time` for deterministic outputs.

## 6. CI

`.github/workflows/programme-review.yml` runs on push-to-main and
on `workflow_dispatch`. It runs on a github-hosted ubuntu-24.04
runner and **never** fails for missing live runtime evidence —
absences become `insufficient_history` / `unknown` / `not_started`
labels in the resulting bundle.

## 7. Honesty rules

* Static-only evidence never silently aggregates with bag-backed.
* Mixed-origin samples are explicitly labelled (`origin_mix_label`).
* Operator review completion never inferred — incident reports
  must declare `review_completion_status = completed`.
* Missing history is reported, not synthesised.
* Subsystem risk reports observations and frequencies, never
  causation or blame.
* Trends are deterministic projections, not forecasts.

## 8. Phase 11 reviewer export

Phase 11 packages the programme-review outputs (plus replay
analytics, incident index, reliability impact, and traceability)
into reviewer-friendly CSV / JSONL / JSON Schema / notebook
artefacts. See [docs/REVIEWER_EXPORTS.md](REVIEWER_EXPORTS.md).

## 9. Phase 13 live runtime input

Phase 13 introduces the live-runtime evidence pipeline. When real
bag-backed live runs land in `evidence/runtime/<run_id>/`, they
flow through incident reconstruction, replay review, replay
analytics, reliability impact, and into programme review — without
any change to programme-review's contracts. Honesty rules
continue to apply: `static_only` and `missing_bag` flags propagate
verbatim, `causality_claimed=false` remains pinned in
subsystem-risk outputs, and `not_executed` runs surface as
`insufficient_history` rather than being synthesised. See
[docs/LIVE_RUNTIME_EVIDENCE_PIPELINE.md](LIVE_RUNTIME_EVIDENCE_PIPELINE.md).

## 10. Related documents

- [docs/GOVERNANCE_HEALTH_MODEL.md](GOVERNANCE_HEALTH_MODEL.md)
- [docs/RELIABILITY_TREND_ANALYSIS.md](RELIABILITY_TREND_ANALYSIS.md)
- [docs/EVIDENCE_FRESHNESS_POLICY.md](EVIDENCE_FRESHNESS_POLICY.md)
- [docs/SUBSYSTEM_RISK_AGGREGATION.md](SUBSYSTEM_RISK_AGGREGATION.md)
- [docs/RELIABILITY_IMPACT_ANALYSIS.md](RELIABILITY_IMPACT_ANALYSIS.md)
- [docs/REPLAY_ANALYTICS.md](REPLAY_ANALYTICS.md)
- [docs/CI_RELIABILITY_GATE.md](CI_RELIABILITY_GATE.md)
- [docs/LIVE_RUNTIME_EVIDENCE_PIPELINE.md](LIVE_RUNTIME_EVIDENCE_PIPELINE.md)
- [docs/LIVE_RUNTIME_MATURITY_REPORT.md](LIVE_RUNTIME_MATURITY_REPORT.md)
- [docs/GOVERNED_MISSION_REHEARSAL.md](GOVERNED_MISSION_REHEARSAL.md) —
  Phase 16 rehearsal analytics feed programme review through the same
  filesystem layout as Phase 8 analytics, but every artefact is
  labelled `simulated` so trends never silently mix simulated with
  bag-backed evidence.
