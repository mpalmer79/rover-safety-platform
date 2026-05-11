# Mission Intent Grammar

Phase 14A. The platform is **not safety-certified**. This document
enumerates the **closed** set of supported natural-language
constructs. Anything not on this list is recorded as
`unsupported_instruction` and never translated into a mission
objective.

## 1. Normalisation

Before pattern matching, the parser:

1. lower-cases the input,
2. collapses runs of whitespace,
3. replaces `!` and `?` with `.`,
4. splits on sentence-ending punctuation (`. ` / `; `) and the
   conjunctions ` and `, ` then `, ` also `.

`1.0` and `1.5 m/s` are preserved (period inside a number is not
treated as a sentence boundary).

## 2. Supported templates

Each row is one template. The compiler accepts **only** clauses
matching one of these patterns.

### Objectives

| Template id | Example phrasings |
| --- | --- |
| `move_to_target` | `go to waypoint bravo`, `drive to bravo`, `head to zone alpha` |
| `patrol_area` | `patrol area patrol_loop_a`, `patrol the patrol_loop_b` |
| `inspect_zone` | `inspect zone inspection_zone_north`, `inspect the loading_zone_two` |
| `return_to_dock` | `return to dock`, `return home`, `dock` |
| `wait_for_condition` | `wait for clearance`, `hold until clearance` |
| `pause_at_checkpoint` | `pause at checkpoint bravo` |
| `terminate_mission` | `terminate mission`, `abort mission`, `stop` |

### Constraints

| Template id | Example phrasings |
| --- | --- |
| `avoid_region` | `avoid region maintenance_bay`, `stay out of human_only_zone`, `do not enter waypoint alpha` |
| `restricted_corridor_avoidance` | `avoid restricted corridors`, `stay clear of restricted corridor` |
| `speed_limit` | `limit speed to 1.0 m/s`, `do not exceed 1.5 m/s`, `speed limit 1 m/s` |
| `time_window` | `operate only during daylight`, `operate during night only` |
| `safe_stop_on_trigger` | `safe-stop on lidar stale`, `safe-stop if odom diverges` |
| `recovery_directive_return_to_dock` | `return to dock if lidar health degrades`, `if battery low return to the dock` |
| `continue_under_degraded` | `continue under degraded conditions`, `proceed in degraded mode` |

## 3. Slot normalisation

Slot extractors strip locator prefixes so equivalent phrasings
produce equivalent slots:

| Prefix | Stripped to |
| --- | --- |
| `waypoint X` | `X` |
| `zone X` | `X` |
| `area X` | `X` |
| `region X` | `X` |
| `checkpoint X` | `X` |

This means *drive to waypoint alpha* and *drive to alpha* produce
the same objective.

## 4. Ambiguity phrases

Any slot value (or full clause) containing one of these phrases is
recorded as `ambiguous_destination` / `ambiguous_clause` and the
clause goes to `rejected_clauses`:

`somewhere near`, `around the`, `near the`, `approximately near`,
`approximately at`, `in the general area`, `wherever`, `anywhere`,
`kind of near`, `sort of`.

## 5. Dangerous phrases (always rejected)

Any clause containing one of these substrings is rejected with
`dangerous_unsupported_instruction`:

`run shell`, `execute python`, `execute code`, `rm -rf`,
`shutdown the rover`, `disable safety`, `bypass supervisor`,
`override safety`, `ignore safety`, `open browser`, `open ssh`,
`curl `, `wget `.

## 6. Examples by status

| Status | Input | Why |
| --- | --- | --- |
| `compile_ok` | `Drive to waypoint bravo. Return to dock.` | Two accepted clauses, no warnings. |
| `compile_ok_with_warnings` | `Drive to bravo. Do silly thing.` | First clause accepted; second is `unsupported_instruction` warning. |
| `compile_ambiguous` | `Inspect the area near loading.` | Contains `near the` / `near loading`; flagged but not safety-failing. |
| `compile_rejected` | `Drive to restricted_corridor_one.` | ODD violation: prohibited region. |
| `compile_rejected` | `Run shell command rm -rf /.` | Dangerous phrase. |
| `compile_rejected` | `Drive to alpha. Do not enter alpha.` | Contradiction. |

## 7. Adding a template

Adding a template is a **deliberate, reviewable** change:

1. Add a new `Template(...)` entry to `templates.py`.
2. Map its id to a stage or constraint kind in `constraints.py`.
3. Add at least one test in `backend/tests/test_natural_language_mission.py`.
4. Update this document.

## 8. Related documents

- [`NATURAL_LANGUAGE_MISSION_COMPILER.md`](NATURAL_LANGUAGE_MISSION_COMPILER.md)
- [`MISSION_ASSURANCE_MODEL.md`](MISSION_ASSURANCE_MODEL.md)
