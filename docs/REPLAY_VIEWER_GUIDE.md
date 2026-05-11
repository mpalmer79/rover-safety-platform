# Replay Viewer Guide (Phase 17A)

The platform is **not safety-certified.** This page documents the
Phase 17A replay viewer at `apps/mission-control/src/app/replay/`
and the per-mission detail page at
`apps/mission-control/src/app/missions/[id]/`.

## 1. Replay index

`/replay` lists every committed `rehearsal-audit.json` under
`mission-rehearsals/audits/`. Each row is a `MissionCard` that
shows:

* the request id and description;
* the final status pill (`completed`, `rejected`, `aborted`);
* the risk band badge;
* the evidence chip (`evidence: simulated · bag-backed: no`);
* the plan and runtime deterministic hashes;
* the audit's `generated_at_utc`.

Rejected and aborted rehearsals are sorted alongside completed
ones. No filter silently drops rejected runs.

## 2. Mission detail

`/missions/<id>` is the centrepiece operator surface. It composes:

1. **Lifecycle stepper.** The deterministic state machine
   (`created → validated → approved → rehearsing → completed`).
2. **Mission plan panel.** Verbatim waypoints, requested topics,
   forbidden topics, and safety constraints from the audit.
3. **`CompilerDecisionCard`.** Validator diagnostics with explicit
   counts and a per-rejection list.
4. **`SupervisorAuthorityPanel`.** Decision status, safety status,
   rationale, rejected reasons, allowed / forbidden topics, human
   review flag, decision timestamp.
5. **`ReplayTimeline`.** Every event from the rehearsal runtime,
   verbatim, with the deterministic hash exposed inline.
6. **Mermaid timeline.** State-machine transitions rendered as
   a Mermaid `flowchart TD`.
7. **`AuditPanel`.** Evidence lineage (hashes, evidence chip,
   disclaimer).
8. **`ReplayAnalyticsPanel`.** Integer counts (rehearsals,
   approved, rejected, aborted, completed, supervisor rejections,
   validator rejections, deterministic replay stable flag).
9. **Replay markers list.** The marker subset of the event stream.

## 3. Honesty rules

* The replay index ALWAYS reports the bundle count alongside
  `simulation-only · bag-backed: 0` so the operator cannot mistake
  this index for a live runtime view.
* The mission detail page renders rejected supervisor decisions in
  red; the rejected-reasons list uses monospaced text in the
  status-rejected colour.
* A rejected mission still gets a `MissionStateStepper`, a
  `CompilerDecisionCard`, and a `SupervisorAuthorityPanel`. No
  panel is hidden because the mission was rejected.
* Replay markers and runtime events preserve the original
  deterministic hashes from the backend artefact.

## 4. What the replay viewer is not

* It is not a live telemetry stream. Pages are statically generated
  at build time.
* It is not a Foxglove replacement. Real bag replay still lives in
  the Phase 7 replay-review pipeline; the Phase 17A replay viewer
  surfaces simulated rehearsal evidence only.
* It is not a deployment surface for real-robot motion. No CTA in
  the viewer triggers a hardware action.

## 5. Future direction

A future phase could:

* embed a Foxglove panel iframe for real bag-backed runs once the
  self-hosted Jazzy runner produces them;
* add a scrubber that walks the event stream by sequence;
* attach Phase 6 incident reconstructions to the audit lineage.

Each of those requires updating the safety-boundary documentation
and the requirements registry before it ships.
