# Working in this repo

Guidance for future Claude Code sessions. Read this once before touching code.

## The one invariant

The safety supervisor has final authority over motion. Mission code may
*request* motion; only `backend/app/safety/supervisor.py` may authorize it.
**Never mutate `SafetyState` outside `backend/app/safety/`.** Every state
transition is reason-coded, allowed-list checked, and replayable. Bypassing
this boundary breaks the architectural thesis of the project.

If you need a new safety state or a new transition: open an ADR in
`docs/adr/` first. Do not just add it.

## Layout

| Path | What lives here |
|---|---|
| `backend/app/safety/` | Supervisor, motion arbitration, freshness, watchdogs, transitions |
| `backend/app/mission/` | Mission orchestrator, waypoint execution, recovery |
| `backend/app/verification/` | Requirements registry, scenario verifier, evidence gen, audits |
| `backend/app/replay/` | Event recording, run manifests |
| `backend/app/world_model/` | Keepout zones, occupancy, snapshots |
| `backend/app/api/` | FastAPI layer |
| `backend/app/domain/` | Pure value objects |
| `apps/mission-control/src/` | Next.js operator UI (read-only; never sends control commands) |
| `apps/mission-control/src/adapters/` | Backend JSON to UI types. Honesty rules live here |
| `rover_ws/src/rover_safety_bridge/` | ROS 2 facade over the supervisor |
| `tools/` | CLI scripts: scenario runs, audits, evidence generation |
| `evidence/`, `incidents/`, `spatial-replay/runs/canonical-fixture/` | Committed baselines. Pytest verifies these. Don't regenerate casually |
| `docs/adr/` | Architectural decisions. Required reading before structural changes |

## Test commands

```bash
# Backend (Python)
cd backend && pytest                  # full suite with coverage gates
cd backend && pytest tests/test_safety_supervisor.py -x

# Frontend
cd apps/mission-control && npm test   # vitest + coverage
cd apps/mission-control && npm run typecheck
cd apps/mission-control && npm run lint

# Scenario suite
python tools/run_scenario_suite.py
python tools/verify_replay_integrity.py
```

Coverage floors in `backend/pyproject.toml` and `apps/mission-control/vitest.config.ts`
are pinned to **observed minus 2**, not aspirational. Don't bump them without
running the suite.

## Conventions

- **Comments**: write a comment only when the *why* is non-obvious. Don't
  restate what the code does. Don't write multi-paragraph module docstrings.
- **No `except Exception:` blocks** unless you log specifically and re-raise,
  or have a written justification. Bare-broad catches hide real bugs.
- **No new top-level docs files** without checking `docs/` for an existing
  home. The repo has ~135 markdown files in `docs/` already; most new
  additions should be sections in existing files.
- **No new `__init__.py` re-export shims**. If you find yourself writing
  `from .x import Y` for 30 symbols, the consumer should import from the
  submodule directly.
- **No em-dashes in code or code comments**. Use `-` or rewrite.
  (Em-dashes in `.md` prose and UI placeholder strings are fine.)
- **Validators are domain-co-located.** Cross-cutting artefact
  validators (run directories, event streams, ROS YAML, URDF, scenario
  suite) live in `backend/app/validation/`. Feature-specific
  validators (a mission proposal validator, a skill-authoring validator,
  etc.) live in their feature subpackage. Don't move feature validators
  into the cross-cutting drawer to cut a count - see
  `docs/adr/ADR-010-validator-module-co-location.md`.

## Honesty rules

The project's whole point is provable safety claims. Concretely:

- Never claim a feature works unless `evidence/scenarios/<id>/evidence.md`
  or a test proves it.
- Never silently swallow validation failures. Status flows through
  `passed | partial | rejected | unverified`.
- Frontend adapters in `apps/mission-control/src/adapters/` must never
  invert or paper over backend "missing data" signals. Render the em-dash
  placeholder for missing fields; never substitute a synthesized default.
- This project is **not safety-certified**. Don't claim it is.

## When you change something architectural

1. Open or update an ADR in `docs/adr/`.
2. Update the relevant doc (most likely `docs/SAFETY_MODEL.md` or
   `ARCHITECTURE.md`).
3. Add or update a scenario in `qualification/scenarios/` if behavior
   changed.
4. Run the scenario suite; commit refreshed evidence under `evidence/`.

## What not to do

- Don't add backwards-compat shims for removed code. Delete cleanly.
- Don't add feature flags for the polish work; change the code.
- Don't reformat large files alongside logic changes (review noise).
- Don't push to `main`. Develop on a branch and open a PR.
