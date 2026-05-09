# Rover Safety Platform — Backend

Deterministic simulation core for the Autonomous Safety Validation Rover Platform.

This package contains the Phase 1A implementation of the platform's core
software foundation: domain models, safety supervisor, motion arbitration,
sensor simulation, fault injection, structured event emission, and
replay-ready run recording.

The package is intentionally framework-light. The core (domain, safety,
simulation, faults, telemetry, replay) has **zero runtime dependencies
outside the Python standard library**. The optional API gateway uses
FastAPI when available.

## Layout

```
backend/
  app/
    domain/        # typed value objects: enums, ids, motion, sensors, events, ...
    safety/        # supervisor, arbitration, freshness, confidence, watchdogs
    simulation/    # deterministic engine, vehicle model, sensor simulator
    faults/        # fault injector and built-in profiles
    telemetry/     # event bus, in-memory store, JSONL run recorder
    replay/        # run manifest, recorder facade, loader
    api/           # optional FastAPI gateway (requires the `api` extra)
  tests/           # unit and integration tests, no external deps
  examples/        # runnable example scripts
  scenarios/       # scenario JSON profiles
```

## Authority Boundaries

The core software enforces the architectural boundaries defined in
`docs/SAFETY_MODEL.md` and `docs/adr/ADR-004-safety-supervisor-authority-model.md`:

- The mission layer publishes `RequestedMotionCommand` only.
- The safety supervisor produces `AuthorizedMotionCommand`.
- The motor / hardware gateway only consumes `AuthorizedMotionCommand`.
- The fault injector alters inputs and timing; it cannot mutate `SafetyState`
  directly. Safety state is owned by the supervisor.

These boundaries are enforced by types, by tests, and by the simulation
engine's wiring — not by convention.

## Running tests

```bash
cd backend
pytest
```

Tests run with no external dependencies.

## Running an example

```bash
cd backend
PYTHONPATH=. python examples/run_nominal.py
PYTHONPATH=. python examples/run_stale_lidar.py
PYTHONPATH=. python examples/run_estop_latched.py
```

Each example writes a replay-ready run directory under `runs/<run_id>/`.
