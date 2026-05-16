# Known Limitations

ProjectBoundary is intentionally narrow. This document records the
boundaries the public deployment honors so that recruiters,
hiring managers, and technical reviewers do not infer claims that the
platform does not make.

## Scope

ProjectBoundary is a **simulation-only mission-validation and
safety-supervisor demonstration platform**. It validates proposed
robot missions, rejects unsafe commands before motion authority,
preserves supervisor authority on every path, and records
deterministic evidence for replay and audit.

## Out of scope

- **No real hardware control.** Nothing in this repository publishes
  to a real `/cmd_vel` topic. The mission-control UI, the proposal
  workbench, the rehearsal runtime, and the demo replay route are all
  simulation-only.
- **Not safety-certified.** No part of this codebase has been
  qualified against an industry safety standard.
- **No live telemetry.** Every value rendered in the public UI comes
  from a committed JSON artifact on disk. The deployed site does not
  hold a websocket open and does not subscribe to a ROS topic. CI
  enforces this via the Phase 20 honesty test.
- **No bag-backed evidence today.** The live-runtime maturity report
  records `bag_backed = 0` and `runner_status = not_established`.
  These are surfaced verbatim. The platform is structured to accept
  bag-backed evidence when it exists, but does not synthesise it.
- **No generated-code execution.** The skill workbench surfaces
  generated candidates as text; the UI never executes them.
- **No cloud LLM calls.** The honesty test bans `openai`,
  `@anthropic-ai/sdk`, and similar SDK imports anywhere in the
  frontend.

## 3D visualization status

- The canonical demo route (`/demo/warehouse-replay`) renders a
  React Three Fiber scene driven by deterministic pose-sample
  artifacts.
- Coordinates come from `spatial-replay/runs/canonical-fixture/`.
  Zone overlays (dock, aisle, pickup, restricted) are illustrative
  layout hints, not surveyed coordinates.
- Per-mission detail pages (`/missions/[id]`) reuse the existing
  `MissionScene` and may render a 2D fallback when a mission lacks a
  registered spatial-replay artifact. The fallback is intentional
  and labeled.
- WebGL is required for the 3D scene. When WebGL is unavailable, the
  demo route falls back to a polished 2D summary that still carries
  mission state, derivation source, and evidence links.

## Static artifact constraints

- All public routes are statically rendered at build time
  (`force-static`). Adding a new mission requires committing the
  rehearsal audit and (optionally) the spatial-replay run, then
  rebuilding.
- The artifact registry under `spatial-replay/registry/` enforces
  expected hashes. Drift between the registry and on-disk bytes
  fails CI.

## What this implies for reviewers

- Treat every "live" looking number as deterministic evidence pulled
  from disk, not real-time telemetry.
- Treat the rover marker as a **derived** ghost, not a real robot
  pose.
- Treat the "Bag-backed evidence count: 0" status as honest; it is
  not a placeholder waiting to be filled in.
