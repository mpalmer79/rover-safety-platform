# Mission Risk Classification

Phase 14A. The platform is **not safety-certified**. Mission risk
classification is a **pure function** of the compiled plan's
structure and the active ODD profile; it does not claim predictive
power.

## 1. Bands

| Band | Score range | Meaning |
| --- | --- | --- |
| `informational` | 0..9 | Trivial, well-bounded mission. |
| `low` | 10..29 | Short, recovery-aware mission. |
| `moderate` | 30..49 | Multi-stage mission; consider reviewer approval. |
| `elevated` | 50..69 | Reviewer approval recommended before execution. |
| `high` | 70..89 | Dry-run in simulation; reviewer approval required. |
| `critical` | 90..100 | Auto-pass is **forbidden**; manual approval required. |

## 2. Drivers

The score starts at 0 and accumulates:

| Driver | Score delta |
| --- | --- |
| Mission complexity (one objective: 0; each extra: +10) | +10/each |
| Extended autonomy stages (patrol / inspect) | +15/each |
| Restricted-corridor avoidance constraint | +20 |
| Time-window constraint | +10 |
| Safety trigger present | +10 |
| Recovery directive present | -5 |
| Speed limit below the ODD limit | -5 |
| Open warning (per warning) | +5 |
| Open rejection (any count) | clamps score to >= 95 (critical) |

The score is clamped to `[0, 100]`.

## 3. Rejections force `critical`

Any rejection diagnostic forces the band to `critical`. This means
ambiguous and contradictory missions always surface as critical and
require manual review, never auto-pass.

## 4. Mitigation recommendations

The compiler emits a list of mitigations when the band is elevated
or higher:

| Band | Mitigation |
| --- | --- |
| `elevated`, `high`, `critical` | supervised operator review before execution |
| `high`, `critical` | dry-run in simulation before live execution |
| (any band with `safety_trigger` but no `recovery_directive`) | attach an explicit recovery directive (e.g. return-to-dock) |

## 5. Required reviewer actions

A `critical` mission emits a required reviewer action:

> manual approval required - critical mission cannot auto-pass

If any compile rejection is present, the compiler additionally
emits:

> resolve compile rejections before submission

## 6. Honest invariants

- Risk scoring is **deterministic**: identical inputs produce
  identical scores.
- Risk scoring never claims predictive accuracy; it only
  characterises plan-structure complexity.
- `critical` missions always carry a reviewer action; the compiler
  never marks a critical mission as passing.

## 7. Related documents

- [`NATURAL_LANGUAGE_MISSION_COMPILER.md`](NATURAL_LANGUAGE_MISSION_COMPILER.md)
- [`MISSION_ASSURANCE_MODEL.md`](MISSION_ASSURANCE_MODEL.md)
