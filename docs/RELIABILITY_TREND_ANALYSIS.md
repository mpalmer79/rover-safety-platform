# Reliability Trend Analysis

Phase 10's trend analyser produces deterministic projections of
recorded history. The layer never forecasts; "trend" means
"classification of the observations we have." The platform is
**not safety-certified**; trends are engineering reliability
material.

## 1. Trend categories

| Category | Rule |
| --- | --- |
| `improving` | last value − first value ≥ 5.0 |
| `degrading` | last value − first value ≤ −5.0 |
| `stable` | absolute delta < 5.0 |
| `volatile` | at least one direction change of ≥ 10.0 between consecutive samples |
| `insufficient_history` | fewer than two available values |

Rolling-3 and rolling-5 categories apply the same rules to the
trailing 3 / 5 values respectively. A long-window `stable` plus a
rolling-3 `degrading` is a meaningful signal.

## 2. Drift severities

| Severity | Trigger |
| --- | --- |
| `critical_regression` | analytics average score moved by ≤ −25 |
| `regression` | analytics average score moved by ≤ −10, or unknown-file count grew by ≥ 3 |
| `warning` | volatility, missing-bag growth, static-only growth, requirement-coverage decline, validation instability |
| `informational` | insufficient history; included so reports document why no drift was detected |

## 3. Determinism

The classifier is pure — the same series always yields the same
category. Tests pin this contract.

## 4. Honesty rules

* No statistical forecasting.
* No regression prediction.
* No interpolated values when samples are missing.
* `insufficient_history` is reported even when the latest sample
  looks alarming on its own.

## 5. Related documents

- [docs/PROGRAMME_REVIEW.md](PROGRAMME_REVIEW.md)
- [docs/GOVERNANCE_HEALTH_MODEL.md](GOVERNANCE_HEALTH_MODEL.md)
- [docs/EVIDENCE_FRESHNESS_POLICY.md](EVIDENCE_FRESHNESS_POLICY.md)
