# Operator Review Experience (Phase 18)

The platform is **not safety-certified.** This document describes
the operator-review storytelling flow added in Phase 18.

## 1. Mission narrative

Every per-mission detail page now starts with the
`MissionStoryPanel`. The panel walks the operator through one
step per lifecycle phase:

```
1. Proposal               → who asked, what they asked for
2. Validation             → validator decision + rejection reasons
3. Supervisor authority   → approved / rejected / needs review
4. Rehearsal              → event count + start/finish timestamps
5. Intervention           → if any supervisor / rejection events
6. Outcome                → completed / rejected / aborted + reason
7. Replay                 → marker count, review status, bag-backed
```

Steps that describe a healthy phase are toned in `green`; warnings
in `yellow`; failures in `red`. The story is derived entirely from
the audit; no step is invented.

## 2. The page composition

```
mission detail
  ├── lifecycle stepper                 (Phase 17A)
  ├── mission flow timeline             (Phase 17B)
  ├── why-rejected drilldown            (Phase 17B; only when rejected)
  ├── mission narrative panel           (Phase 18, NEW)
  ├── tactical / immersive playback     (Phase 18, NEW; with 2D fallback)
  ├── mission route list                (Phase 17B)
  ├── replay confidence panel           (Phase 18, NEW)
  ├── evidence lineage graph            (Phase 18, NEW)
  ├── mission plan card                 (Phase 17A)
  ├── compiler decision card            (Phase 17A)
  ├── supervisor authority panel        (Phase 17A)
  ├── replay timeline                   (Phase 17A)
  ├── audit panel                       (Phase 17A)
  ├── replay lifecycle panel            (Phase 18, NEW)
  ├── deterministic hash chain          (Phase 18, NEW)
  ├── safety zones                      (Phase 17A/B)
  ├── supervisor interventions          (Phase 17B)
  ├── replay analytics                  (Phase 17A)
  └── replay markers                    (Phase 17A)
```

## 3. Honesty in the storytelling

- The narrative panel reads only from the audit; if the audit has
  no runtime, the narrative says "Rehearsal not executed" and the
  step is toned `red`.
- The confidence panel never upgrades a fixture; a fixture is at
  best `medium` confidence.
- The lineage graph names the verbatim upstream source for every
  step.
- The lifecycle ladder reflects the registry; if the registry
  doesn't list the run, the panel renders an honest "Not
  registered" state.

## 4. Visual language

- **Layered depth** — panels use `panel-elevated` / `glass-panel`
  for the immersive components; the 2D panels keep the original
  `panel` class.
- **Accent restraint** — accent colour is reserved for "active"
  states (active scrubber, active mode, reached lifecycle rung).
- **Status colours** — `completed=green`, `pending=yellow`,
  `warning=orange` (NEW in Phase 18), `rejected=red`, `aborted=violet`.
- **Mono everywhere** — hashes, requirement IDs, mode labels, and
  forbidden topics are all mono-typeset for fast scanning.

## 5. Related docs

- `docs/AUTONOMY_UI_DESIGN_SYSTEM.md`
- `docs/IMMERSIVE_MISSION_CONTROL.md`
- `docs/REPLAY_EVIDENCE_LINEAGE.md`
