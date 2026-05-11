# Skill library — Phase 15A

This directory holds the canonical examples and audit bundles for
the Phase 15A deterministic robotics skill authoring workbench.

The platform is **not safety-certified.** These artefacts are
engineering development aids. They do not represent autonomous
execution, safety certification, or regulatory approval.

## Layout

```
skill-library/
  README.md                              this file
  examples/<example_id>.json             canonical request payloads
  audits/<example_id>/                   per-accepted-skill bundles
    request.json
    candidate.json                       (only on rejection bundles)
    generated-skill.json
    code.py                              copyable code text
    safety-review.json
    code-card.json
    diagnostics.json
    skill-report.md
  rejected/<example_id>/                 per-rejected bundle
    request.json
    candidate.json
    diagnostics.json
    rejection-report.md
```

## How they are generated

```
python3 rover_ws/tools/generate_skill_examples.py
```

The generator is deterministic. The same inputs produce
byte-identical output.

## What each canonical example demonstrates

### Accepted (10)

| Example id                       | Skill type                  | Risk band |
|----------------------------------|-----------------------------|-----------|
| `move_forward_6_feet`            | `move_forward_distance`     | guarded   |
| `move_forward_2_meters`          | `move_forward_distance`     | guarded   |
| `rotate_left_90_degrees`         | `rotate_degrees`            | guarded   |
| `rotate_right_45_degrees`        | `rotate_degrees`            | guarded   |
| `stop_immediately`               | `stop_immediately`          | low       |
| `keyboard_forward_binding`       | `keyboard_forward_binding`  | guarded   |
| `controller_stop_button`         | `controller_button_binding` | guarded   |
| `publish_requested_motion`       | `publish_requested_motion`  | guarded   |
| `waypoint_alpha_request`         | `waypoint_request`          | low       |
| `patrol_alpha_beta`              | `patrol_route_template`     | low       |

### Rejected (9)

| Example id                       | Status     | Rejection reason            |
|----------------------------------|------------|-----------------------------|
| `publish_direct_cmd_vel`         | rejected   | direct_actuator_command     |
| `move_forever`                   | rejected   | unbounded_motion            |
| `disable_safety_supervisor`      | rejected   | safety_override             |
| `ignore_estop`                   | rejected   | estop_override              |
| `go_as_fast_as_possible`         | rejected   | unbounded_speed             |
| `spin_motors_directly`           | rejected   | direct_motor_control        |
| `execute_shell_command`          | rejected   | shell_or_code_execution     |
| `ambiguous_move_forward`         | ambiguous  | ambiguous_request           |
| `unknown_basket_request`         | ambiguous  | ambiguous_request           |

Even the accepted examples are only safe *requests*. The safety
supervisor and motion arbitration remain authoritative; no
copy-paste of generated code authorises actuator motion.

## Where to read next

* `docs/ROBOTICS_SKILL_AUTHORING_WORKBENCH.md` — architectural contract.
* `docs/SKILL_TEMPLATE_CATALOG.md` — supported skills + safety constraints.
* `docs/SKILL_SAFETY_BOUNDARY.md` — what the workbench cannot do.
* `docs/CODE_CARD_METADATA.md` — code-card JSON schema for a future UI.
* `docs/FUTURE_LOCAL_LLM_SKILL_PROVIDER.md` — what a follow-up phase
  would need to add to plug in a local LLM (intentionally not
  implemented here).
