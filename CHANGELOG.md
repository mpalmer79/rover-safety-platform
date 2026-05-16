# Changelog

All notable changes are recorded here. Dates are ISO-8601.

## [Unreleased] — Trust-boundary hardening

A focused hardening pass that moves the trust boundary from "asserted
in prose" to "enforced in code at every seam where untrusted data
meets the deterministic core."

- **#1** `/runs/{run_id}` endpoints validate `run_id` against
  `^[A-Za-z0-9_-]{1,128}$` via a FastAPI dependency and confirm the
  joined path stays under `runs_root`; the input is never echoed back.
- **#2** `ScenarioDefinition.__post_init__` bounds `duration_seconds`,
  `time_step_ms`, `total_steps`, and `faults`. `/simulation/run`
  narrows its exception handler, logs server-side, returns a generic
  400, and no longer returns `run_dir`.
- **#3 / #4** `RECOVERY` exits only to `SAFE_STOP`; recovery-validated
  reactivation now flows `RECOVERY → SAFE_STOP → ACTIVE_NORMAL`,
  gated by a `_recovery_validated` flag. E-stop reset requires a
  two-step armed-then-reset sequence; bare resets are refused with
  `safety_transition.refused` / `estop_reset_unsafe`.
- **#5 / #6** Skill-LLM sanitizer reframed as deterrence. The "do not /
  must not / never" exemption is now sentence-scoped; an AST-based
  Python check replaces the regex for the `code` field (catches
  `eval (x)` with a space, `__import__("sub"+"process")`,
  `from anthropic import Anthropic`, `getattr(__builtins__, ...)`,
  `while 1`, `for _ in itertools.count():`, `os.*` outside `os.path`).
  SyntaxError becomes a structured rejection, not a crash.
- **#7** Every third-party GitHub Action is pinned to a 40-char
  commit SHA; `lint-pinned-actions.yml` enforces it in CI.
- **#8** `MotionArbiter` rejects non-finite requested velocities with
  `INVALID_INPUT_ZERO`, so future paths that bypass
  `MotionCommand.__post_init__` cannot authorise non-zero motion.
- **#9** `hashes_match` uses `hmac.compare_digest` so equality is
  constant-time over the encoded digests.
- **#10** `MermaidView` documents that ingested Mermaid source must
  come from checked-in files only — Mermaid's label-escaping is not
  a sandbox.
- **#11** `DANGEROUS_PHRASES` is now explicitly framed as signaling /
  deterrence; the whitelist of templates is the actual enforcement.
- **#12** The FastAPI gateway defaults to binding `127.0.0.1`; a
  non-loopback host requires `--allow-remote`. The startup log makes
  the no-auth assumption explicit.
- **#13** `events.jsonl` is tamper-evident: every event carries
  `prev_event_hash` (SHA-256 of the previous event's canonical bytes),
  the recorder writes `events_chain_tip` / `events_count` to
  `metadata.json` at finalize, and the replay validator emits
  `replay_integrity.chain_broken` on any mismatch / truncation /
  deletion. Canonical bytes use `sort_keys=True,
  separators=(",", ":"), ensure_ascii=False`. Includes the one-shot
  migration script `tools/migrate_event_chain.py` (not wired into CI).
- **#14 / #18** SROS2 enclave configuration committed under
  `rover_ws/sros2/enclaves/`: operator-panel owns the `/operator/*`
  topics, `rover_safety_bridge` owns `/safety/events`, mission-runtime
  owns `/cmd_vel_requested`. Keystore directory is gitignored. Each
  node logs a WARNING on boot when `ROS_SECURITY_ENABLE` is unset.
- **#15** Sensor freshness is now measured against subscriber
  receive-time, never the sender's `header.stamp`. The sender stamp
  is retained as `sender_stamp_ms` for a rate-limited
  `sensor.stamp_skew_excessive` diagnostic only.
- **#16 / #20** Every safety-bridge subscriber callback is wrapped in
  try/except and routes failures through a rate-limited
  `_emit_invalid_input_event` that publishes `safety.invalid_input`.
  The natural-language mission validator now rejects non-finite,
  zero, or negative speed-limit constraints (NaN previously slipped
  through `if limit > odd.speed_limit_mps`).
- **#17** The mission-control loader's `resolveSafeRepoPath` refuses
  registry `relative_path` values that are absolute, contain `..`
  segments, or resolve outside `repoRoot`. The "honest no artifact"
  UI path already handles the null return.
- **#19** `event_recorder` validates its `run_id` parameter against
  the same charset / length policy as the HTTP layer and exits
  non-zero on a misconfigured launch instead of silently sanitising.
  `world_model_node`'s `zones_path` parameter must resolve under the
  repo root.
- **#21** `ScenarioDefinition` declares operational extents
  (`min/max_pose_x/y`); the mission validator rejects poses outside
  those bounds and emits a warning when no extents are declared.
- **#22** `short_hash` docstring is upgraded to DISPLAY ONLY — the
  16-char prefix has only 64 bits of collision resistance and must
  never be used for verification.
