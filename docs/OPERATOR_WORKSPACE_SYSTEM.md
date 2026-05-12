# Operator Workspace System

> Simulation-only · not safety-certified · review-oriented.

## Overview

Phase 20 introduces an **operator workspace system** to Mission Control.
A workspace is a deterministic, JSON-backed preset that declares the
panel set, sizing, default scene camera mode, timeline mode, and
density that an operator or reviewer should see for a given task.

Workspaces are NOT drag/drop dashboards. There is no runtime layout
state; the JSON shape is the single source of truth, and the same
preset always renders the same layout for the same artefacts on disk.

## Six canonical presets

| Preset id              | Audience                  | Default mission                       | Density      |
| ---------------------- | ------------------------- | ------------------------------------- | ------------ |
| `mission-review`       | Operator + reviewer       | `warehouse_pickup_route_alpha`        | standard     |
| `safety-review`        | Safety case reviewer      | `warehouse_pickup_route_alpha`        | standard     |
| `replay-analysis`      | Replay engineer           | `warehouse_pickup_route_alpha`        | dense        |
| `evidence-audit`       | Quality / compliance      | n/a (fleet-level)                     | dense        |
| `fleet-readiness`      | Fleet operator            | n/a (fleet-level)                     | comfortable  |
| `reviewer-walkthrough` | First-time reviewer       | `warehouse_pickup_route_alpha`        | comfortable  |

Each preset is defined in
`apps/mission-control/src/workspaces/presets.ts` and validated by
`apps/mission-control/tests/workspace.test.tsx`.

## Shell composition

Workspaces are rendered by a shared shell composed of:

* `WorkspaceShell` — the outer grid (sidebar + main column).
* `WorkspaceSidebar` — persistent preset navigation on desktop.
* `WorkspaceTopbar` — preset chip, density indicator, honesty pill.
* `WorkspaceStatusStrip` — rehearsal / bag-backed / requirement
  counters derived from disk.
* `WorkspaceBreadcrumbs` — deep-link breadcrumbs.
* `WorkspacePanelGrid` — 12-column desktop grid that consumes the
  preset's panel layout. Panels animate in via Framer Motion using
  the `PANEL_VARIANTS` token.
* `WorkspacePresetSwitcher` — preset list rendered on the index
  page (`/workspaces`).
* `ResponsiveWorkspaceDrawer` — mobile / tablet-portrait drawer
  presenting the same preset list as the desktop sidebar.

## Responsive strategy

* **Desktop (xl, ≥ 1280px)** — 14rem sidebar + 12-column grid.
* **Tablet landscape (lg, 1024px+)** — 14rem sidebar + 12-column grid.
* **Tablet portrait (md, 768px+)** — 12rem sidebar + 6-column grid.
* **Mobile (< md)** — single-column stack with a drawer trigger.

The grid uses `data-col-span` attributes to expose layout shape to
end-to-end tests. There is no horizontal overflow, and the 3D canvas
never clips because workspaces with the `walkthrough-overlay` panel
reserve their own min-height.

## Determinism + honesty

Workspaces NEVER:

* persist drag/drop layout state,
* claim live telemetry,
* fabricate panel data,
* hide rejected / aborted audits,
* recode `bag_backed` or `derivation_source`,
* expose a websocket / EventSource.

Workspaces ALWAYS:

* read from committed JSON artefacts only,
* preserve `final_status`, `safety_status`, `evidence_status`,
  `bag_backed`, and `derivation_source` verbatim,
* render the safety boundary banner at the layout root.

## Adding a new preset

1. Add a new id to `WorkspacePresetId` in `workspaces/types.ts`.
2. Add a new constant in `workspaces/presets.ts` and register it in
   `WORKSPACE_PRESETS` + `WORKSPACE_PRESET_IDS`.
3. Update `tests/workspace.test.tsx` so the determinism test fails
   without the new preset.
4. Add a sidebar icon mapping in `WorkspaceSidebar`.

The static route generator under
`apps/mission-control/src/app/workspaces/[preset]/page.tsx` will
automatically render the new preset.
