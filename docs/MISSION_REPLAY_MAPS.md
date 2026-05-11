# Mission Replay Maps (Phase 17B → 17C)

The platform is **not safety-certified.** Phase 17B layers a
deterministic 2D mission map onto the existing mission detail page.
Operators can now scrub through the audit event stream and see
which waypoint the deterministic state machine reached at each
sequence index. No real telemetry is implied.

**Phase 17C** extends the same page so that, when a committed
spatial-replay artefact exists at
`spatial-replay/runs/<id>/spatial-replay.json`, the playback panel
renders the artefact's trajectory instead of (or in addition to)
the bounded-inputs derivation. The artefact's derivation source
(`bag_backed`, `fixture`, etc.) is rendered verbatim on the map
caption and the playback panel badge. See
`docs/BAG_BACKED_SPATIAL_REPLAY.md` and
`docs/SPATIAL_REPLAY_HONESTY_RULES.md`.

## 1. The detail page composition

```
mission detail (apps/mission-control/src/app/missions/[id]/page.tsx)
├── lifecycle stepper                 (MissionStateStepper)
├── mission flow timeline             (MissionSpatialTimeline)
├── why this was rejected             (WhyRejectedDrilldown, when rejected)
├── left rail
│   ├── playback panel                (MissionPlaybackPanel)
│   │   ├── tactical map              (MissionMap)
│   │   ├── progress strip            (RouteProgressIndicator)
│   │   └── scrubber                  (ReplayScrubber)
│   ├── mission route table           (MissionRouteList)
│   ├── mission plan                  (Panel)
│   ├── compiler decision             (CompilerDecisionCard)
│   ├── supervisor authority          (SupervisorAuthorityPanel)
│   ├── runtime event timeline        (ReplayTimeline)
│   └── runtime state-machine Mermaid (MermaidView)
└── right rail
    ├── audit panel                   (AuditPanel)
    ├── safety + boundary overlays    (SafetyZoneLayer + ZoneBoundaryOverlay)
    ├── supervisor interventions      (SupervisorInterventionOverlay)
    ├── replay analytics              (ReplayAnalyticsPanel)
    └── replay markers                (Panel)
```

## 2. Scrubber semantics

The scrubber's value is a 0-indexed event sequence number. The
playback panel watches the value and:

1. computes the most recent event whose payload references a
   waypoint id (≤ scrubber index);
2. highlights that waypoint on the map;
3. dims event markers beyond the scrubber index.

The scrubber **never** plays back time; it walks the deterministic
sequence. Two operators on the same machine see the same value at
the same index.

## 3. Event projection rules

`projectEvent` reads `event.payload.waypoint_id` from the audit
event. If a string id is present, the marker is placed at the
matching waypoint's position. If the payload has no id, the marker
appears in the event timeline but NOT on the map. The chosen
position carries the event's `deterministic_hash` so a reviewer can
confirm the marker came from the audit.

## 4. Why this is not Foxglove

* Foxglove replays real ROS bag captures. Phase 17B's playback is
  a sequence walker over simulated events.
* Foxglove can render real 3D telemetry. Phase 17B renders SVG only.
* Foxglove streams from disk. Phase 17B reads the audit JSON at
  build time and statically prerenders the route.

A future phase that wires Phase 13's bag-backed lane into the
mission-control UI could embed a Foxglove panel. Until then,
Phase 17B's maps are the operator surface for simulation-only
rehearsals.

## 5. Replay marker honesty

Every replay marker carries the same `deterministic_hash` as the
underlying audit event. The mission map renders the marker without
any transformation; the hash is therefore identical between the
audit JSON, the prerendered HTML, and the live page.

## 6. What rejected missions look like

* `MissionSpatialTimeline` colours rejection events in the rejected
  status colour (red).
* `MissionStateStepper` recolours the stepper to show the halt
  point.
* `WhyRejectedDrilldown` appears at the top of the detail page;
  it carries the verbatim failure reason and a short English
  explainer.
* `MissionPlaybackPanel` still renders — the scrubber walks only
  the events the runtime emitted before rejection.

## 7. What completed missions look like

* The stepper turns each stage green at the right step.
* The map shows the full route.
* The supervisor intervention overlay renders an honest "no
  interventions recorded" placeholder.
* The replay analytics panel reports `completed_count = 1`.
