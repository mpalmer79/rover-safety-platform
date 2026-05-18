"""Phase 6 incident reconstruction.

Reads Phase 3 / 4 / 5 runtime + scenario evidence and emits a
deterministic incident bundle (timeline, causality, classification,
Markdown + JSON report, Foxglove hint, retained-bundle index).

Submodules:

* ``loader`` — defensive evidence reader.
* ``normalizer`` — heterogeneous events to canonical timeline entries.
* ``timeline`` — deterministic ordering and key-event indexing.
* ``causality`` — rule-based chain reconstruction.
* ``classifier`` — severity / outcome / evidence-status.
* ``reporter`` — Markdown + JSON output.
* ``index`` — retained-bundle index.
* ``compare`` — incident-vs-incident comparison.
* ``foxglove`` — replay-hint metadata.
* ``reconstruct`` — end-to-end entry point.

Import from the submodule that owns the symbol; this package no
longer re-exports per ADR-011 and the no-shim rule in CLAUDE.md.
"""
