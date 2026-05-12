# Fleet Review Architecture

> One robot today. Architecture ready for multi-site review.

## Models

`apps/mission-control/src/site/models.ts` declares the canonical
fleet shapes:

* `Site` — top-level review container (zones + robots).
* `Zone` — operations / transit / exclusion / dock-apron classification.
* `Dock` and `Lane` — illustrative location refs, **not surveyed
  coordinates**.
* `RobotProfile` — id, platform, approved ODD profile, bounded
  speed + bounded distance limits.
* `MissionQueueEntry` / `MissionQueue` — queued-mission references,
  each carrying a `readiness` and `readiness_reason`.
* `RobotReadiness` — derived from the latest rehearsal-audit shape.
* `ZoneStatus` — nominal / needs_review / blocked rollup.

The single committed site is exposed via `CANONICAL_SITE` in
`site/data.ts`. The site fixture carries a verbatim disclaimer
`Simulation-only · not surveyed coordinates · not safety-certified`
that propagates through `FleetOverviewPanel`.

## Readiness derivation

`deriveRobotReadiness({ hasAudit, finalStatus, ... })` is a pure
function. It never recodes the input:

| Input                         | Output state          |
| ----------------------------- | --------------------- |
| `hasAudit` is `false`         | `evidence_missing`    |
| `finalStatus === "rejected"`  | `blocked`             |
| `finalStatus === "aborted"`   | `blocked`             |
| `finalStatus === "completed"` | `ready_to_rehearse`   |
| otherwise                     | `needs_review`        |

This logic is asserted by `tests/fleet.test.tsx`.

## Panel inventory

* `FleetOverviewPanel` — site label, description, ready/blocked
  counts, and the simulation-only disclaimer.
* `SiteMapOverview` — illustrative zone list with dock + lane
  counts. Renders `illustrative · not surveyed coordinates`
  inline.
* `MissionQueuePanel` — queued missions with readiness chips.
* `RobotReadinessCard` — bounded-speed / bounded-distance limits,
  last rehearsal status, open issues, readiness reason.
* `ZoneStatusPanel` — zone-level status + verbatim forbidden
  topics.

## Honesty rules

* Site, zone, dock, and lane coordinates are illustrative. The
  panel chrome states this on every render.
* Robot readiness is computed strictly from rehearsal-audit
  records on disk. No runtime telemetry contributes.
* `forbidden_topics` for every zone is rendered verbatim. The
  exclusion zone always blocks both `/cmd_vel` and
  `/cmd_vel_requested`.
* No mission queue entry implies a scheduled execution. The queue
  is a review reference.
