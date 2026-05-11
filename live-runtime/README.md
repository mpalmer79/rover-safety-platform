# Live Runtime Activation Assets

This directory holds the configuration that a self-hosted ROS 2
Jazzy + Gazebo Harmonic runner needs in order to produce real,
bag-backed runtime evidence for this repository.

The platform is **not safety-certified.** This directory exists to
make a self-hosted run reproducible and to keep evidence honest.

## Layout

```
live-runtime/
  README.md                          (this file)
  runner-profile.template.json       canonical, honest, committed template
  runner-profile.local.example.json  filled-out example (uncommitted variant)
  runner-profile.local.json          OPTIONAL, gitignored, local override
  scenario-plans/
    smoke-live-runtime.yaml          short bring-up + bag capture
    core-live-qualification.yaml     longer scenario that exercises safety
  baselines/
    README.md
    maturity-baseline.template.json  honest "not_established" template
    maturity-baseline.json           OPTIONAL, generated after a real run
```

## Workflow

1. Copy `runner-profile.template.json` to `runner-profile.local.json`
   on the self-hosted runner. Update `runner_id`, `workspace_path`,
   and any host-specific values.
2. Run the one-command pipeline:
   ```
   python3 rover_ws/tools/run_live_runtime_pipeline.py \
     --scenario-plan live-runtime/scenario-plans/smoke-live-runtime.yaml \
     --runner-profile live-runtime/runner-profile.local.json \
     --output evidence/runtime/<run_id>
   ```
3. Inspect the generated `evidence.md`, `evidence.json`, and
   `bag-manifest.json`. Only a `bag_backed` outcome can update the
   maturity baseline.
4. Promote the maturity baseline only after a passing bag-backed run:
   ```
   python3 rover_ws/tools/run_live_runtime_pipeline.py \
     --runner-profile live-runtime/runner-profile.local.json \
     --output evidence/runtime/<run_id> \
     --promote-baseline
   ```

See `docs/SELF_HOSTED_JAZZY_RUNNER_SETUP.md` for the full runner
setup, `docs/LIVE_BAG_CAPTURE_RUNBOOK.md` for the bag capture
procedure, and `docs/LIVE_RUNTIME_EVIDENCE_PIPELINE.md` for the
end-to-end pipeline.
