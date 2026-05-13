# Enterprise Operator UX

> Designed for review consoles, not dashboards.

## Reference points

Mission Control aims at the operational UX bar set by:

* NASA Open MCT
* Foxglove Studio
* Boston Dynamics Orbit
* Anduril Lattice
* Palantir Foundry mission consoles

These are not entertainment apps. They prioritise:

* Architectural clarity over visual novelty
* Evidence provenance over decoration
* Safety boundaries over conversion
* Operator-density layouts over white-space-first marketing pages
* Honest data over fabricated indicators

## Phase 20 contribution

Phase 20 brings Mission Control to that bar by:

* Introducing six deterministic workspace presets (mission review,
  safety review, replay analysis, evidence audit, fleet readiness,
  reviewer walkthrough).
* Adding twelve telemetry-density panels that derive every value
  from committed JSON.
* Adding a reviewer walkthrough overlay that explains the system
  end-to-end in ten deterministic steps.
* Promoting a shared design-system module so typography, spacing,
  motion, surfaces, and accessibility are tokenised.
* Honesty CI gates that prevent reintroduction of websockets,
  EventSource, `bag_backed: true` literals, or `WebSocket(` calls.

## What this UX does NOT do

* Stream live telemetry.
* Open a ROS websocket bridge.
* Implement drag/drop persistence.
* Fabricate runtime state.
* Imply autonomous execution authority.
* Imply safety certification.

These boundaries are intentional. A reviewer from a robotics or
aerospace safety team should immediately recognise the discipline.

## Operational tone

* Colour palette is muted operator-aerospace, not "gamer RGB".
* Motion is short and purposeful (`PANEL_VARIANTS`, `STEP_VARIANTS`).
* Status badges never overstate. `rejected` stays `rejected`;
  `bag_backed: false` renders `false` everywhere.
* The safety banner is mounted at the root layout and is never
  suppressed by any workspace.

## Where to look first

1. Open `/walkthrough` and step through the ten-step explainer.
2. Open `/workspaces/safety-review` to inspect the supervisor
   authority, validation outcomes, and forbidden topics.
3. Open `/workspaces/evidence-audit` to inspect the artifact
   registry integrity rollup.
4. Open `/workspaces/fleet-readiness` to see the multi-site
   architecture (with one robot today).
