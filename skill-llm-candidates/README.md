# Skill-LLM candidates — Phase 15B

This directory holds the canonical examples, audit bundles, and
provider configurations for the Phase 15B *local* LLM skill
candidate provider.

The platform is **not safety-certified.** Local LLM providers are
**disabled by default**. Phase 15B does not call any cloud API, does
not execute generated code, and does not publish to any ROS topic.

## Layout

```
skill-llm-candidates/
  README.md                                this file
  config/
    provider.disabled.json                 default; always not_configured
    provider.fixture.json                  deterministic offline provider
    provider.local_http.example.json       OPT-IN example; not enabled
    provider.ollama.example.json           OPT-IN example; not enabled
    provider.llama_cpp.example.json        OPT-IN example; not enabled
  examples/<fixture_id>.json               request payload + expected status
  audits/<fixture_id>/                     per-candidate audit bundle
    request.json
    provider-result.json
    sanitizer-result.json
    validator-result.json
    candidate.json                          (only when provider proposed)
    safety-review.json                      (only when fully accepted)
    code-card.json                          (only when fully accepted)
    llm-candidate-report.md
```

## Fixture set

| Fixture id                              | Kind                  | Final status                |
|-----------------------------------------|-----------------------|------------------------------|
| `fixture_valid_move_forward_6_feet`     | valid                 | `accepted`                   |
| `fixture_valid_stop_immediately`        | valid                 | `accepted`                   |
| `fixture_valid_rotate_90_degrees`       | valid                 | `accepted`                   |
| `fixture_direct_cmd_vel`                | sanitizer-rejected    | `sanitizer_rejected`         |
| `fixture_infinite_loop`                 | sanitizer-rejected    | `sanitizer_rejected`         |
| `fixture_shell_command`                 | sanitizer-rejected    | `sanitizer_rejected`         |
| `fixture_network_call`                  | sanitizer-rejected    | `sanitizer_rejected`         |
| `fixture_safety_override`               | sanitizer-rejected    | `sanitizer_rejected`         |
| `fixture_secret_leak`                   | sanitizer-rejected    | `sanitizer_rejected`         |
| `fixture_missing_stop_command`          | validator-rejected    | `validator_rejected`         |
| `fixture_missing_timeout`               | validator-rejected    | `validator_rejected`         |
| `fixture_unbounded_speed`               | validator-rejected    | `validator_rejected`         |
| `fixture_external_provider_disabled`    | external-disabled     | `validator_rejected`         |

Every audit bundle carries the verbatim Phase 15B safety
disclaimer. Even the accepted bundles cannot authorise actuator
motion; only the runtime safety supervisor can.

## How to regenerate

```
python3 rover_ws/tools/generate_skill_llm_examples.py
```

The generator is deterministic — repeated runs with the same
`--generated-at` produce byte-identical files.

## How to run one candidate

```
python3 rover_ws/tools/propose_robotics_skill_with_local_llm.py \
  --text "Stop the robot immediately" \
  --provider fixture \
  --fixture-id fixture_valid_stop_immediately \
  --output skill-llm-candidates/audits/manual_stop \
  --generated-at 2026-05-13T00:00:00+00:00
```

For local providers:

```
python3 rover_ws/tools/propose_robotics_skill_with_local_llm.py \
  --text "Move forward 6 feet" \
  --provider local_http \
  --config skill-llm-candidates/config/provider.local_http.example.json \
  --allow-local-provider \
  --output skill-llm-candidates/audits/manual_local_http
```

Even with `--allow-local-provider`, Phase 15B does **not** call the
network. The audit records that the policy was satisfied; a future
phase must add the actual transport.

## Where to read next

* `docs/LOCAL_LLM_SKILL_PROVIDER.md` — architectural contract.
* `docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md` — what the provider
  cannot do.
* `docs/LOCAL_LLM_SKILL_PROMPT_CONTRACT.md` — JSON-only prompt
  contract for a future local model.
* `docs/SKILL_LLM_CANDIDATE_AUDITS.md` — audit bundle schema.
* `docs/FUTURE_LOCAL_MODEL_OPERATIONS.md` — operational plan for the
  follow-up phase that wires up a real local model.
