# Live Runtime Maturity Baseline

This directory holds the live-runtime maturity baseline for the
project. The baseline answers a single question:

> Has this repository ever produced a real bag-backed live runtime
> evidence record?

The platform is **not safety-certified.** This baseline is engineering
maturity tracking and nothing more.

## Files

* `maturity-baseline.template.json` — the canonical, honest template
  used when no live run has occurred. The committed baseline must
  remain `not_established` until a real bag-backed run exists.
* `maturity-baseline.json` — OPTIONAL. Created (and overwritten) by
  `rover_ws/tools/run_live_runtime_pipeline.py --promote-baseline`
  after a passing bag-backed run on a self-hosted runner.

## Promotion rule

A baseline can be promoted to `status: established` only when:

1. a `LiveRuntimeEvidence` record exists with `mode: bag_backed`,
2. the bag manifest is `bag_backed`,
3. the runner profile is qualified or provisional and recorded the
   bag-backed run id, and
4. all required topics from the scenario plan are observed in the
   bag inventory.

Any weaker shape leaves the baseline at `not_established`. Do not
hand-edit the baseline; let the pipeline manage it.
