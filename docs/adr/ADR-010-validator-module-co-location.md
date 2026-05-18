# ADR-010: Validator Module Co-Location

## Status
Accepted

## Context

`CLAUDE.md` carried a long-standing note that the repository has
"15 separate validators across subpackages, and consolidating them
is a tracked refactor." The polish-pass PR 4 plan accordingly listed
"merge 15 scattered validator modules → 3" as an architectural
sub-task.

A full inventory of every file named `*validator*.py` finds 16
modules across the backend:

Under `backend/app/validation/` (cross-cutting drawer):

- `mission_validator.py` — mission run-directory checks layered on
  the generic replay validator.
- `replay_validator.py` — generic run-directory + event-stream
  structural validation against the replay contract.
- `event_validator.py` — standalone events.jsonl validator used by
  the `tools/validate_event_integrity.py` CLI.
- `safety_pipeline_validator.py` — in-process scenario runner that
  asserts motion-arbitration invariants.
- `bridge_validator.py` — YAML-only audit of the `ros_gz_bridge`
  configuration against ADR-004 / `docs/SAFETY_MODEL.md`.
- `tf_validator.py` — URDF / TF tree structural check.
- `scenario_suite.py` — Phase 1C deterministic scenario gate.

Co-located with their feature packages:

- `mission_proposal/validator.py` — structural validation of
  proposal dicts (shape only; safety is the sanitizer's job).
- `natural_language_mission/validator.py` — ODD / feasibility /
  recovery / contradiction checks over an extracted NL mission.
- `mission_rehearsal/rehearsal_validator.py` — pre-supervisor
  structural validation of a rehearsal plan.
- `replay_review/validator.py` — Phase 3 replay-review check
  emission.
- `reviewer_exports/validator.py` — strict honesty-rule audit of
  reviewer export bundles.
- `skill_authoring/validator.py` — static safety tripwires for
  LLM-generated skill code.
- `skill_llm_provider/validator_bridge.py` — bridge that invokes
  the skill_authoring validator from the LLM provider pipeline.
- `spatial_replay/validator.py` — describe-don't-upgrade audit of an
  assembled spatial-replay artefact.
- `runtime_validation/static_validator.py` — workspace static
  checks (topics declared, TF frames present, etc.) that fall back
  when ROS isn't installed.

These modules share **no validation logic**: each implements
bespoke checks over a different artefact family (mission requests,
replay artefacts, ROS config, URDF, skill code, etc.). The earlier
"consolidate to 3" goal was framed by count rather than purpose, and
following it would force one of:

1. A central `validation/` package that imports from every feature
   package, inverting the dependency graph and coupling cross-cutting
   utilities to feature-specific logic.
2. A magic dispatcher that picks the right validator at runtime,
   adding indirection without removing any of the underlying check
   code.
3. A single mega-module that pretends unrelated checks share a
   home, hurting discoverability.

None of these is an improvement.

## Decision

The validator layout is deliberate and correct as-is:

1. **`backend/app/validation/`** is the home for **cross-cutting
   artefact validators** — checks that operate on artefacts the
   safety / replay / mission subsystems all produce or consume
   (run directories, event streams, ROS configuration, URDF, the
   scenario suite). New cross-cutting validators belong here.
2. **Feature subpackages** own validators that exercise their own
   domain models or generated artefacts. A `mission_proposal`
   validator lives inside `mission_proposal/`; a `skill_authoring`
   validator lives inside `skill_authoring/`. Domain validators
   import from their feature package only — they do not become
   peers of cross-cutting validators.

The "consolidate 15 → 3" task is **closed**. It will not be done.
`CLAUDE.md` is updated to reflect this rule rather than the
deferred-refactor language it carried before.

## Consequences

### Positive

- The dependency graph stays clean: `validation/` does not depend
  on feature packages, and feature packages do not depend on each
  other's validators.
- Discoverability improves: a contributor changing
  `mission_proposal` code finds the relevant validator in the same
  directory, not in a central drawer.
- No CI churn from a large refactor that would have touched ~16
  modules and their tests for no net change in behavior.

### Negative

- The repository continues to carry many files named
  `*validator*.py`. The lexical similarity may invite future
  consolidation pitches; this ADR is the answer to those pitches.
- A new contributor counting files may still see "15 validators"
  and wonder if there is duplication. The CLAUDE.md update and the
  charter docstring in `app/validation/__init__.py` exist to
  forestall that.

## Boundary cases

A validator that does not belong in any feature package and does
not validate a cross-cutting artefact is rare but possible. When
one arises, prefer adding it to `backend/app/validation/` and
documenting the call site in this ADR rather than inventing a new
top-level subpackage. Validators that genuinely span more than one
domain (e.g., a check that asserts a mission_proposal artefact
matches its rehearsal plan) belong in `backend/app/validation/`
because the cross-domain coupling is the validator's purpose.

## References

- `CLAUDE.md` — repo conventions and the "no new validator module"
  rule.
- `backend/app/validation/__init__.py` — charter docstring.
- `docs/SAFETY_MODEL.md` — origin of the bridge and TF validation
  rules.
- ADR-004 — supervisor authority model that the bridge validator
  enforces.
