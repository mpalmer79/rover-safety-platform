# Live Runner Profile

A *runner profile* is a JSON document that describes one self-hosted
GitHub Actions runner attached to this repository. The profile is
the chokepoint that prevents an unattached or unqualified runner
from claiming live evidence.

The platform is **not safety-certified.** Profiles document
engineering qualification, not certification.

## Schema

```jsonc
{
  "runner_id": "rover-runner-01",                    // required
  "runner_status": "unqualified",                    // unqualified | provisional | qualified
  "qualification_status": "not_executed",            // passed | failed | partial | not_executed
  "labels": ["self-hosted", "ros-jazzy", "gazebo"],  // ALL three required
  "host_os": "Ubuntu 24.04 LTS",
  "ros_distro": "jazzy",
  "gazebo_version": "harmonic",
  "python_version": "3.12",
  "workspace_path": "/home/runner/rover_ws",
  "bag_format": "mcap",                              // "mcap" | "db3"
  "last_qualified_at": null,                         // ISO-8601 or null
  "last_qualified_run_id": null,
  "last_bag_backed_run_id": null,
  "known_limitations": ["..."],
  "notes": ["..."]
}
```

## Files

| File                                            | Role                                                                                    |
|-------------------------------------------------|-----------------------------------------------------------------------------------------|
| `live-runtime/runner-profile.template.json`     | committed; honest template; remains `unqualified`                                       |
| `live-runtime/runner-profile.local.example.json`| committed example showing a populated `provisional` profile                             |
| `live-runtime/runner-profile.local.json`        | gitignored; the per-runner real profile created on the self-hosted host                 |

## Validation rules

The `validate_runner_profile` helper enforces:

* `runner_id` is non-empty;
* labels include `self-hosted`, `ros-jazzy`, and `gazebo`;
* labels do NOT include any GitHub-hosted label
  (`ubuntu-latest`, `ubuntu-24.04`, `windows-latest`, `macos-latest`);
* `bag_format` is `mcap` or `db3`;
* if `runner_status == qualified`:
  * `qualification_status == passed`,
  * `last_qualified_at` is set,
  * `last_qualified_run_id` is set,
  * a `last_bag_backed_run_id` is recorded (or supplied as
    out-of-band evidence to the validator);
* if `runner_status == provisional`, `qualification_status` is
  `partial` or `passed`;
* if `runner_status == unqualified`, `qualification_status` cannot
  be `passed`;
* timestamps (when present) are ISO-8601.

The committed CI test
`backend/tests/test_live_runtime.py::test_committed_runner_profile_is_honest`
asserts that the committed template never claims qualification
without bag-backed evidence.

## Promotion lifecycle

```
unqualified
    │
    │ first dry-run + first attempt at smoke scenario plan
    ▼
provisional / partial
    │
    │ first bag_backed live run with all required topics observed
    ▼
qualified / passed (and last_bag_backed_run_id set)
```

Demotion on failure is OK and expected — flip the local profile
back to `provisional` if a follow-up run fails.

## Operational guidance

* Edit the local profile only on the self-hosted host. Never commit
  `runner-profile.local.json`.
* Do not record secrets in the profile. The schema deliberately has
  no fields for tokens, keys, or credentials.
* The pipeline will run with the committed template if no local
  profile is found — but the template is `unqualified`, so all runs
  will report `mode: not_executed`. This is the honest fall-back.
