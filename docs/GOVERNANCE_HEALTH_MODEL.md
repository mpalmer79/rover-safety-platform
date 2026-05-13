# Governance Health Model

This document describes the six-discipline rollup produced by
`backend/app/programme_review/governance_health.py`. The platform
is **not safety-certified**; governance health is engineering
reliability material.

## 1. Disciplines

| Category | What it measures | Source artifacts |
| --- | --- | --- |
| `evidence` | Replay-review evidence ingestion + static-vs-bag-backed mix. | replay-review-report.json |
| `replay` | Replay quality + drift severity. | analytics-report.json, drift-report.json |
| `ci` | CI gate outcomes (passed / warning / failed). | impact-report.json gate_decision |
| `traceability` | Mapped REQ-* ids in the latest impact bundle. | impact-report.json requirement_impacts |
| `runtime_qualification` | Qualification summary outcomes. | qualification-summary.json |
| `review_completion` | Operator review acknowledgements. | incident-report.json review_completion_status |

## 2. Per-discipline rating

Each discipline returns one of:

| Rating | Meaning |
| --- | --- |
| `strong` | Best signal observed (no failures, no degradation). |
| `acceptable` | Some warnings / some static-only / a single qualification miss. |
| `weak` | Recurring warnings, declining coverage, or a single critical input. |
| `concerning` | Repeat failures, contradictions, or replay honesty violations. |
| `unknown` | No artifacts in this discipline yet. |

## 3. Overall programme health

Worst-discipline-wins with one exception: every-discipline-unknown
falls back to `weak` (a fresh repo is not automatically `strong`).

| Worst discipline rating | Overall |
| --- | --- |
| `concerning` | `concerning` |
| `weak` | `weak` |
| `acceptable` | `acceptable` |
| `strong` | `strong` |
| all `unknown` | `weak` |

## 4. Honesty rules

* The model never reports `strong` when every discipline is
  `unknown`.
* The model records the **reasons** behind each rating and the
  triggering artifacts (paths or labels).
* Drift severity drives the `replay` discipline rating; static
  drift (no history) is `unknown`, not `weak`.

## 5. Related documents

- [docs/PROGRAMME_REVIEW.md](PROGRAMME_REVIEW.md)
- [docs/RELIABILITY_TREND_ANALYSIS.md](RELIABILITY_TREND_ANALYSIS.md)
- [docs/RELIABILITY_IMPACT_ANALYSIS.md](RELIABILITY_IMPACT_ANALYSIS.md)
