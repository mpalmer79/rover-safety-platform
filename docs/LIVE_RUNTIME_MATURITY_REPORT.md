# Live Runtime Maturity Report

This page summarises the live runtime maturity of this repository.
It is updated by `rover_ws/tools/run_live_runtime_pipeline.py`
whenever the pipeline runs with `--promote-baseline` and observes a
genuinely bag-backed live run.

The platform is **not safety-certified.** This page tracks
engineering qualification maturity — whether real, reproducible
self-hosted live evidence exists for this repository.

## Current status

| Field                  | Value                                                  |
|------------------------|--------------------------------------------------------|
| Status                 | `not_established`                                      |
| Reason                 | no bag-backed live run has been captured against this branch |
| Bag-backed runs        | 0                                                      |
| Last run id            | _none_                                                 |
| Last run at            | _none_                                                 |
| Last runner id         | _none_                                                 |
| Last scenario plan id  | _none_                                                 |
| Source baseline        | `live-runtime/baselines/maturity-baseline.template.json` |

The committed baseline (`maturity-baseline.template.json`) holds the
canonical `not_established` value. The promoted baseline
(`maturity-baseline.json`) is gitignored — promote it on the
self-hosted runner, copy it back into a review PR explicitly when
publishing maturity.

## Promotion criteria

The pipeline will promote the baseline to `established` only when
**all** of the following hold for the same run:

1. `LiveRuntimeEvidence.mode == bag_backed`;
2. the bag manifest is `bag_backed` (metadata + non-empty chunks);
3. the runner profile is at least `provisional`;
4. the runner profile records the bag-backed run id;
5. all required topics from the scenario plan are observed in the
   bag inventory.

Anything weaker leaves the baseline at `not_established`. Do not
hand-edit the baseline.

## Maturity tiers

| Tier                    | What it means                                                                                  |
|-------------------------|------------------------------------------------------------------------------------------------|
| `not_established`       | no bag-backed live run has been observed; CI can only prove static-source / static-workspace.  |
| `established` (smoke)   | one bag-backed run of `smoke-live-runtime` exists.                                              |
| `established` (core)    | one bag-backed run of `core-live-qualification` exists.                                         |
| `recurring`             | bag-backed runs are produced regularly (e.g. weekly) on a stable runner; manually tracked.     |

The pipeline only manages the binary `not_established` /
`established` distinction. Reviewers must read the baseline plus
recent `evidence/runtime/<run_id>/evidence.md` files to attribute
the higher tiers.

## Honest reporting

This page must remain `not_established` until a real bag-backed run
is observed. If you find this page claiming `established` without a
matching bag-backed `evidence.json`, treat it as a regression and
revert to the template.
