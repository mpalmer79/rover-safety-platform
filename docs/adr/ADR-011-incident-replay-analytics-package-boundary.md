# ADR-011: incident_analysis / replay_analytics Package Boundary

## Status
Accepted

## Context

The polish-pass PR 4 plan listed "consolidate `incident_analysis/`
and `replay_analytics/`" as an architectural sub-task. A full
inventory of both packages reveals the consolidation goal was
formulated on filename overlap (`loader.py`, `models.py`, `index.py`
in both) rather than on what each package actually does.

The two packages cleanly represent two distinct phases of the
post-run analysis pipeline:

### `backend/app/incident_analysis/` — Phase 6: incident reconstruction

Reads Phase 3 / 4 / 5 runtime evidence (`events.jsonl`,
`safety-transition-audit.json`, `command-audit.json`, scenario
evidence) and reconstructs an incident bundle:

- `loader.py` — defensive reader for runtime + scenario evidence.
- `normalizer.py` — heterogeneous events → canonical timeline entries.
- `timeline.py` — deterministic ordering, relative times, key events.
- `causality.py` — rule-based chain reconstruction.
- `classifier.py` — severity, outcome, evidence-status derivation.
- `reporter.py` — Markdown + JSON incident bundles.
- `index.py` — enumerate retained incident bundles.
- `compare.py` — incident-vs-incident comparison.
- `foxglove.py` — replay-hint metadata.
- `reconstruct.py` — end-to-end entry point.

Output: `incident-report.{json,md}`, `timeline.{json,md}`,
`foxglove-hint.json`, `incident-index.{json,md}`.

### `backend/app/replay_analytics/` — Phase 8: replay analytics

Reads the Phase 6 incident bundle **and** the Phase 7 replay-review
artefacts and derives quality metrics across incidents:

- `loader.py` — defensive reader for replay bundles (different
  input set: incident bundles + replay manifests, not runtime
  evidence).
- `coverage.py` — coverage metrics (deterministic float scores).
- `scoring.py` — quality scoring with confidence bands.
- `recommendations.py` — gap-grounded recommendations.
- `trends.py` — cross-incident trend table.
- `comparison.py` — cross-incident comparison enriched with
  replay-quality columns (extends the Phase 6 comparator).
- `review_audit.py` — explicit acknowledgement audit.
- `index.py` — filterable analytics index across incidents.
- `reporting.py` — aggregate / gap / trends / per-incident reports.

Output: `replay-analytics-{aggregate,gap,trends,per-incident}.md`,
`replay-quality-index.json`, `review-audit.{json,md}`.

The two layers share **no logic**. Their loaders read different
artefacts. Their `models.py` files declare different domain types
(`Incident`, `IncidentTimeline`, `CausalityChain` vs
`ReplayCoverageReport`, `ReplayQualityScore`, `ReplayTrend`). Their
indexes index different things (incident bundles vs analytics
overlays). The filename overlap is superficial — common Python
module names that recur in any layered package.

A consolidation would have to either:

1. **Collapse the phase boundary** by merging both into a single
   `post_run_analysis/` package. This loses the documented Phase 6
   / Phase 8 distinction, which is referenced from the requirements
   registry (`backend/app/verification/requirements.py`), the
   evidence pipeline (`docs/EVIDENCE_FRESHNESS_POLICY.md`), and the
   ROADMAP.
2. **Force file renames** (`incident_loader.py`, `replay_loader.py`
   inside one package) without changing any behavior — pure churn.
3. **Invert the dependency** so a wrapper package depends on both —
   adds indirection, removes nothing.

None of these is an improvement.

## Decision

The package boundary is deliberate and stays:

1. **`backend/app/incident_analysis/`** owns Phase 6 incident
   reconstruction. Its inputs are runtime + scenario evidence; its
   outputs are incident bundles.
2. **`backend/app/replay_analytics/`** owns Phase 8 analytics. Its
   inputs are Phase 6 incident bundles + Phase 7 review artefacts;
   its outputs are quality metrics, trends, and reports.

The packages are documented as a pipeline rather than as two
overlapping silos.

### Side effect: drop the re-export shims

`CLAUDE.md` forbids `__init__.py` files that re-export 30+ symbols.
Both packages currently violate the rule (`incident_analysis`:
41 re-exports; `replay_analytics`: 28). The only consumers of those
shims are the two test files. This PR slims both `__init__.py`
files to a one-line docstring and updates the test files to import
from the submodules where the symbols actually live.

## Consequences

### Positive

- Phase 6 / Phase 8 boundary stays visible in the package layout.
- Import sites in tests now point at the module that owns each
  symbol, which makes navigation and refactoring easier.
- `incident_analysis/__init__.py` and `replay_analytics/__init__.py`
  stop violating the "no re-export shim" rule.
- No production behavior changes; the package APIs are unchanged.

### Negative

- The two `__init__.py` files no longer support
  ``from app.incident_analysis import X`` for arbitrary X. New
  consumers must import from the submodule, e.g.,
  ``from app.incident_analysis.models import Incident``. This is
  the documented convention, but is a small ergonomic cost for
  shell-level exploration.

## References

- `CLAUDE.md` — "No new `__init__.py` re-export shims" rule.
- `backend/app/incident_analysis/` and `backend/app/replay_analytics/`.
- `docs/EVIDENCE_FRESHNESS_POLICY.md` — phase-pipeline reference.
- ADR-010 — sister decision for the validator packages.
