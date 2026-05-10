# Reliability baselines

This directory pins the canonical replay analytics state used by
the Phase 9 reliability impact analyser
(`backend/app/reliability_impact/analytics_delta.py`).

The baseline contains:

* `replay-quality-index.baseline.json` — pin of
  `incidents/analytics/replay-quality-index.json` at the moment
  the baseline was captured;
* `replay-analytics-report.baseline.json` — pin of
  `incidents/analytics/replay-analytics-report.json` at the same
  moment.

The analyser compares the **current** analytics outputs to the
**baseline** values and classifies the differences:

* **improvement** — newer artefacts moved in the right direction
  (higher score, better coverage, more replay evidence);
* **neutral** — no material change;
* **warning** — small regression (score drop ≥ 10 within the same
  band);
* **regression** — larger regression (score drop ≥ 25 or coverage
  band drop);
* **critical_regression** — score crossed below 40, contradictions
  appeared, replay honesty was violated, or a bag-backed run
  reverted to missing-bag without explanation.

## Updating the baseline

Baselines are managed **intentionally**. CI never auto-updates the
files in this directory.

To capture a fresh baseline after an analytics regen, run:

```bash
python3 rover_ws/tools/analyze_source_impact.py \
  --changed-files . \
  --write-baseline \
  --output reliability-impact/
```

`--write-baseline` copies the current
`incidents/analytics/replay-quality-index.json` and
`incidents/analytics/replay-analytics-report.json` files into
this directory. Commit the result alongside the analytics regen
that caused the change.

## Why this is honest

* The baseline is a pinned snapshot. Comparisons are deterministic.
* When a baseline file is missing the analyser reports a
  **warning**, not a failure (so the first run on a fresh clone is
  not broken).
* Static-only incidents stay static-only in the baseline; the
  delta engine never promotes a static-only baseline into a
  missing-bag failure in the current run.
