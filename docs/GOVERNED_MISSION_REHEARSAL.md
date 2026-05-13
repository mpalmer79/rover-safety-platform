# Governed Mission Rehearsal (Phase 16)

The platform is **not safety-certified.** Phase 16 connects the
deterministic mission compiler, the validator + sanitizer
chokepoints, the safety supervisor authority gate, an explicit
state machine, the replay system, and the analytics system into a
single *simulation-only* rehearsal pipeline.

> **No real robot moves. No network call occurs. No bag exists.**
> The runtime safety supervisor and motion arbitration remain
> authoritative for any future real run.

## 1. The architecture in one diagram

```
   operator natural-language request
                │
                ▼
   Phase 15B local LLM proposal seam (disabled by default)
                │
                ▼
   Phase 14B / 15A / 15B sanitizer (forbidden phrase chokepoint)
                │
                ▼
   Phase 14A mission compiler  →  mission graph
                │
                ▼
   mission_rehearsal.build_plan      (deterministic value object)
                │
                ▼
   mission_rehearsal.validate_plan   (per-waypoint safety rules)
                │
                ▼
   mission_rehearsal.review_plan     (supervisor authority gate)
                │
                ▼
   mission_rehearsal.run_rehearsal   (deterministic state machine)
                │
                ▼
   replay bridge + analytics bridge  (read-only artifacts)
                │
                ▼
   audit bundle (simulation-only)
```

The runtime safety supervisor and motion arbitration are NOT
invoked at runtime in Phase 16. The rehearsal layer *simulates* the
authority chain by emitting `MOTION_REQUEST_SIMULATED` events and
recording an explicit supervisor decision. Real-robot authority
remains with the runtime supervisor.

## 2. Modules

| Module                                                      | Role                                                       |
|-------------------------------------------------------------|------------------------------------------------------------|
| `backend/app/mission_rehearsal/models.py`                   | dataclasses + status / failure / event enums                |
| `backend/app/mission_rehearsal/rehearsal_state_machine.py`  | explicit transition map + `StateMachineError`              |
| `backend/app/mission_rehearsal/rehearsal_safety.py`         | bounded-motion limits + forbidden-pattern scan              |
| `backend/app/mission_rehearsal/rehearsal_plan.py`           | deterministic plan builder + hash                          |
| `backend/app/mission_rehearsal/rehearsal_validator.py`      | per-waypoint + per-topic validation                         |
| `backend/app/mission_rehearsal/rehearsal_supervisor.py`     | authoritative decision gate                                 |
| `backend/app/mission_rehearsal/rehearsal_events.py`         | deterministic event factory                                 |
| `backend/app/mission_rehearsal/rehearsal_runtime.py`        | state-machine driver + event stream                         |
| `backend/app/mission_rehearsal/rehearsal_capture.py`        | filter / count helpers                                      |
| `backend/app/mission_rehearsal/rehearsal_timeline.py`       | Markdown + Mermaid timeline renderer                        |
| `backend/app/mission_rehearsal/rehearsal_replay_bridge.py`  | replay bundle (never bag-backed)                            |
| `backend/app/mission_rehearsal/rehearsal_analytics_bridge.py`| per-rehearsal analytics                                    |
| `backend/app/mission_rehearsal/rehearsal_audit.py`          | audit bundle builder + Markdown renderer                    |
| `backend/app/mission_rehearsal/rehearsal_reporter.py`       | filesystem reporter                                         |

## 3. Determinism

Every output is deterministic:

* `MissionRehearsalPlan.deterministic_hash` is a SHA-256 prefix
  over the request id, mission id, proposal source, waypoint list,
  safety constraints, requested / forbidden topic lists, and seed.
* `MissionRehearsalEvent.deterministic_hash` covers the event
  sequence, type, subtype, severity, description, and payload.
* `MissionRehearsalEvent.event_time_ns` is `sequence × 100 ms`; no
  wall-clock time enters the event stream.
* `MissionRehearsalRuntime.deterministic_hash` ties the plan hash,
  the seed, the final status, and every event hash together so a
  reviewer can confirm the run reproduces.

## 4. State machine

See `docs/MISSION_REHEARSAL_STATE_MACHINE.md` for the full
transition table. Illegal transitions raise
`StateMachineError`; legal ones are recorded as events.

## 5. Replay + analytics

The replay bundle records `evidence_status='simulated'` and
`bag_backed=False`. The analytics result distinguishes
approved / rejected / aborted / completed rehearsals plus the
supervisor and validator rejection counts. No probabilistic
analytics; no AI-generated conclusions.

## 6. CLIs

```
rover_ws/tools/run_mission_rehearsal.py
    --mission mission-rehearsals/examples/<id>.json
    --output mission-rehearsals/audits/<id>
    [--seed 42]
    [--generated-at <iso8601>]

rover_ws/tools/validate_mission_rehearsal.py
    --audit mission-rehearsals/audits/<id>/rehearsal-audit.json

rover_ws/tools/generate_rehearsal_examples.py
    [--examples-dir mission-rehearsals/examples]
    [--audits-dir mission-rehearsals/audits]
    [--generated-at 2026-05-13T00:00:00+00:00]

rover_ws/tools/generate_rehearsal_replay.py
    --audit mission-rehearsals/audits/<id>/rehearsal-audit.json
```

## 7. Authority statement

The Phase 16 pipeline is simulation-only and does NOT authorise
live robot execution or safety certification. The runtime safety
supervisor and motion arbitration are the only paths to actuator
authority. A future phase that wires Phase 16 to a real robot must
update `docs/FUTURE_DIGITAL_TWIN_DIRECTION.md` and add an ADR.
