# Reliability Impact Analysis

This document describes the Phase 9 source-to-evidence
reliability-impact layer. The platform is **not safety-certified**;
the analysis is engineering reliability material.

## 1. What this layer answers

> _What changed, what subsystem did it affect, what evidence was
> impacted, and did replay quality or safety validation regress?_

It does so by walking the chain:

```
source code changes
 -> affected subsystem
 -> affected requirement IDs
 -> affected tests + evidence artefacts
 -> affected replay analytics (vs baseline)
 -> reliability risk + CI gate decision
```

## 2. Architectural principle

The layer is **read-only** with respect to source code, evidence
artefacts, and replay analytics. It inspects, classifies, and
reports. It never mutates source code, never fabricates git
history, and never auto-updates baselines.

## 3. Modules

Under `backend/app/reliability_impact/`:

| Module | Role |
| --- | --- |
| `models.py` | Typed dataclasses + controlled enums (`ChangeType`, `Subsystem`, `RiskLevel`, `GateStatus`, `DeltaSeverity`). |
| `git_changes.py` | Change inventory: `--changed-files`, `git diff base..head`, working-tree fallback, CI env helper. |
| `subsystem_classifier.py` | Deterministic path-prefix classifier. Unknown paths map to `unknown` (never dropped). |
| `requirement_mapper.py` | Subsystem -> live `REQ-*` ids from `app.verification.requirements`. |
| `evidence_mapper.py` | Subsystem -> recommended tools + artefacts to regenerate. |
| `analytics_delta.py` | Per-incident + aggregate delta against the pinned baseline. |
| `risk_assessor.py` | Conservative `RiskLevel` rules. |
| `baseline.py` | Resolution + intentional baseline write helpers. |
| `ci_gate.py` | Deterministic gate decision (independent of risk level). |
| `report.py` | Markdown + JSON renderer + bundle writer. |

## 4. CLIs

| Tool | Purpose |
| --- | --- |
| `rover_ws/tools/analyze_source_impact.py` | Run the analysis, write the bundle under `reliability-impact/`. |
| `rover_ws/tools/reliability_impact_gate.py` | Read the bundle, emit the gate decision (exit 0/1). |

## 5. Output layout

Per run (`reliability-impact/` or `reliability-impact/<id>/`):

* `impact-report.md` / `.json`
* `changed-files.json`
* `subsystem-impact.json`
* `requirement-impact.json`
* `evidence-impact.json`
* `analytics-delta.json`
* `gate-decision.json`

## 6. Status vocabularies

### Risk level (informational)

| Level | Meaning |
| --- | --- |
| `none` | nothing flagged |
| `low` | documentation / test only, or a few unknown files |
| `moderate` | safety path touched with recipe; analytics warning; CI workflow modified |
| `high` | safety path with no evidence recipe; static workflow removed; analytics regression |
| `critical` | critical analytics regression or replay honesty violation |

### Gate status (CI exit signal)

| Status | Exit |
| --- | --- |
| `passed` | 0 |
| `warning` | 0 |
| `failed` | 1 |
| `not_executed` | 0 |

The gate is **independent of risk level** — a `high` risk run may
still pass the gate when none of the documented failure conditions
fire. The gate is the hard signal; risk is the human-readable
summary.

### Delta severity

| Severity | Meaning |
| --- | --- |
| `improvement` | newer artefacts moved in the right direction |
| `neutral` | no material change |
| `warning` | score drop ≥ 10 within the same band; small coverage drop |
| `regression` | score drop ≥ 25 or coverage band drop ≥ 2 |
| `critical_regression` | score crossed below 40, contradictions appeared, replay honesty violated, or bag-backed reverted to missing without explanation |

## 7. Honesty rules

- Missing live runtime evidence on a github-hosted runner is **never**
  a failure. The gate honours the documented exception.
- Missing baseline is a **warning**, not a failure.
- Static-only -> static-only is **neutral**.
- Bag-backed -> missing_bag without metadata is **critical**.
- `evidence_origin` flipping from `scenario-evidence` to `bag-backed`
  while `bag_status` stays `missing_bag` is a **critical honesty
  violation**.
- Unknown files are surfaced, never silently ignored.

## 8. CI

`.github/workflows/reliability-impact.yml` runs on every PR (and on
`workflow_dispatch`) on a github-hosted runner. It checks out with
full history, collects changed files from `pull_request.base`,
regenerates replay analytics best-effort, runs the source impact
analysis, and gates the build using the impact report.

## 9. Baselines

See [docs/CI_RELIABILITY_GATE.md](CI_RELIABILITY_GATE.md) and
`reliability-baselines/README.md` for baseline management. Baselines
are managed **intentionally** via `--write-baseline` — CI never
auto-updates them.

## 10. Related documents

- [docs/SOURCE_TO_EVIDENCE_TRACEABILITY.md](SOURCE_TO_EVIDENCE_TRACEABILITY.md)
- [docs/CI_RELIABILITY_GATE.md](CI_RELIABILITY_GATE.md)
- [docs/REPLAY_ANALYTICS.md](REPLAY_ANALYTICS.md)
- [docs/REPLAY_QUALITY_SCORING.md](REPLAY_QUALITY_SCORING.md)
- [docs/TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md)
