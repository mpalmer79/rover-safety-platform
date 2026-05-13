# Reviewer Experience Audit

This document records the reviewer-experience pass that landed under
the `claude/optimize-portfolio-site-geJXz` branch and gives future
contributors a clear picture of what changed, why, and what is still
open.

## Goals

The deployed `apps/mission-control` Next.js site is read by recruiters,
hiring managers, technical screeners, and senior engineers. The
previous build leaked internal build-stage labels (`Phase 19`,
`Phase 17A`, `Phase 14A`), forced first-time visitors into dense
engineering surfaces with no on-ramp, and did not provide a polished
3D / visual demonstration in the public flow.

The goals of this pass were:

1. Give a first-time reviewer a **30-second understanding** of what
   ProjectBoundary is, what it proves, and where to click first.
2. **Remove internal build-stage terminology** from the public chrome
   without breaking the engineering data model.
3. Provide a **polished 3D mission-replay demo** that creates
   immediate visual impact while remaining honest, deterministic,
   and artifact-backed.
4. Replace **broken / internal-flavored fallback pages** with
   reviewer-friendly recovery paths.
5. Preserve the simulation-only safety boundary, supervisor authority
   language, and deterministic artifact behavior.

## Issues identified

| # | Issue | Surface |
|---|-------|---------|
| 1 | Sidebar chrome announced "Phase 19" / "Phase 17A" as the platform identity | `src/components/ResponsiveShell.tsx`, `src/components/SiteNav.tsx` |
| 2 | Safety Authority diagram referenced the internal "Phase 14A compiler" | `src/app/safety/page.tsx` |
| 3 | Workbench narrative referenced the internal "Phase 15A workbench" | `src/app/workbench/page.tsx` |
| 4 | Not-found page led with "No artefact at this path" / pipeline language | `src/app/not-found.tsx` |
| 5 | No public Start Here on-ramp; reviewers landed on a dense dashboard | (new route) |
| 6 | No canonical 3D demo route; the existing 3D scene was buried inside per-mission pages | (new route) |
| 7 | Major pages led with technical detail, not value | dashboard, replay, safety, walkthrough, workbench, evidence, workspaces |
| 8 | Safety banner copy was negative-only ("not certified, not bag-backed") | `src/components/SafetyBoundaryBanner.tsx` |

## Fixes shipped

- **Renamed the public chrome** to "ProjectBoundary · Mission Control"
  and reordered navigation around the reviewer flow (Start Here →
  Mission Replay Demo → Safety Authority → Walkthrough → Evidence &
  Audit → Mission Control → Replay Viewer → Workspaces → Workbench →
  Component Catalog).
- **Replaced internal phase labels** in user-facing copy:
  - `Phase 19` → `ProjectBoundary · Mission Control`
  - `Phase 17A` → `ProjectBoundary · Mission Control`
  - `Phase 14A compiler` → `Deterministic mission compiler`
  - `Phase 15A workbench` → `deterministic skill workbench`
  Internal source comments and engineering documentation still use
  the phase identifiers; only public-facing copy was rewritten.
- **Added `/start`**, a hero landing page that opens with what
  ProjectBoundary demonstrates, lists the recommended reviewer path,
  and offers four primary CTAs. See `src/app/start/page.tsx`.
- **Added `/demo/warehouse-replay`**, the canonical 3D mission replay
  experience. The route loads the canonical fixture spatial-replay
  artifact and the alpha rehearsal audit, then drives an animated
  rover through committed waypoints with a play/pause control,
  timeline scrubber, narrative beats, and evidence links. The 3D
  scene is dynamic-imported, gated on WebGL support, and falls back
  to a polished 2D summary when WebGL is unavailable.
- **Rewrote the not-found page** to present curated reviewer paths
  instead of internal pipeline language.
- **Added "What this proves" panels** to the dashboard, safety,
  replay, walkthrough, workbench, evidence, and workspaces pages.
- **Reframed the safety boundary banner** to combine the
  simulation-only / not-safety-certified boundary with what the
  platform demonstrates.

## Tests added

- `tests/reviewer-experience.test.tsx` — pins the navigation chrome,
  not-found fallback, safety-banner copy, and Start Here landing.
- `tests/warehouse-replay-demo.test.tsx` — pins the demo controls,
  reviewer copy, evidence links, descriptor, and the absence of raw
  missing-artifact failure copy on the public route.

The full suite remains green: 33 test files / 374 tests pass after
this pass (up from 31 / 351 on `main`).

## Remaining limitations

- The 3D scene relies on WebGL via React Three Fiber. The demo route
  ships with a polished 2D fallback; reviewers on a WebGL-disabled
  browser will see the fallback, not the 3D scene.
- The `Component Catalog` route exists and is wired into navigation
  but is positioned last because its primary audience is engineering
  reviewers, not recruiters.
- Some engineering-detail components (`EvidenceLineageGraph`,
  `ReplayConfidencePanel`, `PoseTracePanel`) still surface the literal
  string "No spatial-replay artefact" inside per-mission detail
  panels. These are honest fallbacks and remain pinned by
  `tests/artifact-lineage.test.tsx`. The canonical demo route never
  hits this state because the canonical fixture is registered.
- The dashboard still labels its summary panel "not_established" for
  live-runtime maturity, which is the verbatim deterministic value
  from the artifact. This is intentional honesty; the new What this
  proves panels explain it.

## Follow-up priorities

1. Add a screenshot-based visual regression for `/demo/warehouse-replay`.
2. Wire `/demo/warehouse-replay` into the bundle-budget check.
3. Add a second canonical demo mission (rejected mission) so the demo
   route can illustrate the rejection path visually.
4. Translate the "What this proves" copy into a reusable component
   so future pages do not need to inline panels.
