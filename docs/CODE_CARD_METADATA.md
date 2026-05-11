# Code Card Metadata

The platform is **not safety-certified.** This document describes
the ``CodeCard`` payload that the Phase 15A workbench attaches to
every generated skill. The payload exists so a future reviewer UI
can render copyable code blocks with safety badges and animated
typing — without Phase 15A adding any frontend dependency.

## Schema

```jsonc
{
  "title": "string",                  // human-readable title
  "subtitle": "string",               // one-line summary
  "language": "python_ros2",          // SkillLanguage value
  "skill_type": "move_forward_distance",
  "code": "string",                   // full rendered code text
  "line_count": 0,                    // splitlines() length
  "copy_label": "string",             // UI button label
  "safety_badges": [                  // ordered set of badge tokens
    "requested-motion-only",
    "supervisor-authorised",
    "risk:guarded",
    "not-safety-certified"
  ],
  "animation_steps": [                // ordered UI typing sequence
    "imports",
    "constants",
    "publisher setup",
    "bounded command loop",
    "stop command",
    "safety explanation"
  ],
  "risk_band": "guarded",             // SkillRiskBand value
  "diagnostics": [...]                // structured diagnostics
}
```

The Python representation is `app.skill_authoring.models.CodeCard`.

## Where it appears

* on the in-memory ``GeneratedSkill`` value object
  (`generated_skill.code_card`);
* on disk, as `<bundle_dir>/code-card.json`;
* inside `<bundle_dir>/generated-skill.json` (the audit JSON
  embeds the card so a single file is self-contained);
* inside `<bundle_dir>/skill-report.md` (the title, subtitle, code,
  and safety badges are rendered as Markdown for human review).

## Animation steps

Each step is a short token a future UI can map to:

* `imports` — highlight the `import` statements;
* `constants` — highlight the named constants block;
* `publisher setup` — highlight the publisher / topic construction;
* `bounded command loop` — highlight the duration / count / watchdog
  controlled loop;
* `stop command` — highlight the final zero `Twist`;
* `safety explanation` — highlight the comment header that names
  the safety supervisor;
* `single publish` — single-shot publication (no loop);
* `mission request` — mission-request templates;
* `context manager entry` / `user-callable body` / `zero-on-exit`
  — safe-stop wrapper templates.

A UI is free to ignore unknown tokens. The set is intentionally
small.

## Safety badges

Every card carries:

* `requested-motion-only` (or `mission-request-only` for mission
  templates);
* `supervisor-authorised`;
* `risk:low` / `risk:guarded` / `risk:restricted` / `risk:blocked`;
* `not-safety-certified`.

These tokens are deterministic; new badges may only be added by
modifying `app/skill_authoring/diagnostics.py` and shipping a test
that asserts the new label.

## Determinism

The card payload depends only on the parsed parameters, the
template, and the rendered code. With a fixed `--generated-at`,
two runs produce byte-identical `code-card.json` and
byte-identical `generated-skill.json`.
