# Reviewer Exports

Phase 11 packages the existing engineering evidence into reviewer-
friendly formats: CSV, JSONL, JSON Schema, a manifest, a notebook,
and a Markdown summary. The platform is **not safety-certified**;
the export is engineering review material.

## 1. What ships

| Path | Purpose |
| --- | --- |
| `reviewer-export/manifest.json` | Single source of truth: tables, row counts, schema paths, csv paths, jsonl paths, disclaimer. |
| `reviewer-export/reviewer-export-summary.md` | Human-readable overview: what the export contains + how to read evidence origins. |
| `reviewer-export/schemas/*.schema.json` | JSON Schema per table. |
| `reviewer-export/csv/*.csv` | CSV per table. |
| `reviewer-export/jsonl/*.jsonl` | Line-delimited JSON per table. |
| `reviewer-export/notebooks/reviewer_walkthrough.ipynb` | Reviewer notebook scaffold. |
| `reviewer-export/notebooks/README.md` | Notebook usage instructions. |

## 2. Tables

The exporter emits eight tables. Their canonical fields are pinned
in `backend/app/reviewer_exports/models.py` and mirrored by the
schemas under `reviewer-export/schemas/`:

| Table | Source | Notes |
| --- | --- | --- |
| `programme_health` | `programme-review/programme-review.json` | One row per discipline / reason. |
| `trend_series` | `programme-review/trend-report.json` | Three windows per series (`full`, `rolling_3`, `rolling_5`). |
| `drift_findings` | `programme-review/drift-report.json` | One row per finding. |
| `subsystem_risk` | `programme-review/subsystem-risk-report.json` | `causality_claimed=false` always. |
| `gate_history` | `programme-review/gate-history.json` | One row per gate status (passed / warning / failed / not_executed). |
| `replay_quality` | `incidents/analytics/replay-quality-index.json` | `static_only` / `missing_bag` flags preserved. |
| `incident_index` | `incidents/index.json` | Per-incident severity / outcome / evidence status. |
| `requirement_coverage` | `verification/traceability.json` | REQ-* ids + mapped tests / artefacts. |

## 3. Architectural principle

The layer is **read-only**. It transforms existing artefacts into
reviewer-friendly formats. It never:

* invents data;
* infers causality;
* claims safety certification;
* hides missing evidence;
* upgrades static-only to live;
* aggregates across origin classes without labelling the mix.

## 4. Honesty rules

* `causality_claimed` is **always `false`** in the subsystem-risk
  table.
* `static_only=true` and `missing_bag=true` flags ride along on
  every replay-quality row whose source bag status matches.
* Missing source artefacts result in zero-row tables; the manifest
  records the absence.
* Every reviewer-facing artefact carries the verbatim certification
  disclaimer.

## 5. CLIs

| Tool | Purpose |
| --- | --- |
| `rover_ws/tools/generate_reviewer_export.py` | Build the bundle. |
| `rover_ws/tools/validate_reviewer_export.py` | Validate an existing bundle. |

Both CLIs are deterministic given the same inputs + an explicit
`--generated-at` timestamp.

## 6. CI

`.github/workflows/reviewer-export.yml` runs on push and PR. It
generates the bundle, validates it, and uploads the directory as a
workflow artefact. It does not require ROS, Gazebo, Foxglove, or
live runtime evidence.

## 7. Related documents

- [docs/EXPORT_SCHEMA_REFERENCE.md](EXPORT_SCHEMA_REFERENCE.md)
- [docs/REVIEWER_NOTEBOOK_GUIDE.md](REVIEWER_NOTEBOOK_GUIDE.md)
- [docs/PROGRAMME_REVIEW.md](PROGRAMME_REVIEW.md)
- [docs/REPLAY_ANALYTICS.md](REPLAY_ANALYTICS.md)
- [docs/RELIABILITY_IMPACT_ANALYSIS.md](RELIABILITY_IMPACT_ANALYSIS.md)
- [docs/TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md)
