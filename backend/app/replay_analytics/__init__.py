"""Phase 8 replay analytics.

Reads Phase 6 incident bundles + Phase 7 review artefacts and emits
coverage metrics, quality scores, gap recommendations, trends, and
the per-incident / aggregate reports.

Submodules:

* ``loader`` — defensive replay-bundle reader.
* ``coverage`` — deterministic coverage metrics.
* ``scoring`` — quality bands + confidence.
* ``recommendations`` — gap-grounded recommendations.
* ``trends`` — cross-incident trend table.
* ``comparison`` — cross-incident comparison enriched with replay
  quality columns.
* ``review_audit`` — explicit-acknowledgement review audit.
* ``index`` — filterable analytics index.
* ``reporting`` — aggregate / gap / trends / per-incident reporting.

Import from the submodule that owns the symbol; this package no
longer re-exports per ADR-011 and the no-shim rule in CLAUDE.md.
"""
