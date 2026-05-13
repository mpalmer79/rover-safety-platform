# Reviewer Notebook Guide

The reviewer notebook (`reviewer-export/notebooks/reviewer_walkthrough.ipynb`)
is a thin tour of the CSV files emitted by the Phase 11 export. It
loads the data and shows simple counts + previews — no charts, no
ML, no live runtime evidence. The platform is **not safety-certified**;
this guide is engineering review material.

## Prerequisites

Open the notebook in Jupyter, VS Code, or `nbviewer`. The notebook
uses only the Python standard library; pandas and matplotlib are
imported behind guards so the notebook still runs without them.

## Layout

The notebook expects to be opened from
`reviewer-export/notebooks/`. CSV files live alongside under
`../csv/`:

```
reviewer-export/
  notebooks/
    reviewer_walkthrough.ipynb
    README.md
  csv/
    programme_health.csv
    replay_quality.csv
    incident_index.csv
    drift_findings.csv
    subsystem_risk.csv
    requirement_coverage.csv
    trend_series.csv
    gate_history.csv
```

If you move the notebook or the CSV files, edit the `CSV_DIR`
constant at the top of the notebook accordingly.

## What it shows

For each table the notebook:

1. Loads the CSV into a list of dicts (or a `pandas.DataFrame` if
   pandas is available).
2. Prints the row count.
3. Shows a 5-row preview.

The order matches the export tables: programme health, replay
quality, incidents, drift findings, subsystem risk, requirement
coverage, trend series, gate history.

## How to interpret the data

* **Programme health** — six discipline ratings rolled up into the
  programme-level rating (`strong` / `acceptable` / `weak` /
  `concerning` / `critical`).
* **Replay quality** — per-incident scores and bag/origin labels.
  Treat `static_only=true` and `missing_bag=true` rows as
  evidence-limited; never as live-runtime.
* **Incident index** — severity / outcome / evidence status.
* **Drift findings** — emitted by the Phase 10 drift detector;
  severity is one of `informational`, `warning`, `regression`,
  `critical_regression`.
* **Subsystem risk** — frequency and severity per subsystem.
  `causality_claimed=false` always; the export never asserts
  causation.
* **Requirement coverage** — REQ-* ids with mapped tests and
  artifacts. `coverage_status` ∈ `covered`, `tests_only`,
  `evidence_only`, `unmapped`.
* **Trend series** — per-metric trend categories with rolling-3 /
  rolling-5 windows. `insufficient_history` means the underlying
  programme review had fewer than two samples for the metric.
* **Gate history** — pass / warning / failure counts plus the
  volatility label.

## What it does not do

* No network calls.
* No ROS, Gazebo, or Foxglove imports.
* No causal inference.
* No predictive ML.
* No matplotlib by default — if the environment has matplotlib the
  reviewer can add their own cells; the shipped scaffold doesn't
  rely on it.

## Honesty rules

The notebook preserves every honesty rule established by earlier
phases:

* Static-only stays static-only;
* Missing-bag stays missing-bag;
* `causality_claimed` stays `false`;
* `insufficient_history` is rendered as such and never forecast.

## Related documents

- [docs/REVIEWER_EXPORTS.md](REVIEWER_EXPORTS.md)
- [docs/EXPORT_SCHEMA_REFERENCE.md](EXPORT_SCHEMA_REFERENCE.md)
- [docs/PROGRAMME_REVIEW.md](PROGRAMME_REVIEW.md)
