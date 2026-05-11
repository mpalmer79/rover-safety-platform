# LLM Repair Suggestions (Phase 19)

The platform is **not safety-certified.** Repair suggestions are
*never* auto-applied. The repair surface exists so an operator
reading a rejected candidate can see exactly what is wrong and
edit the source themselves.

## 1. Suggestion shape

```ts
{
  code: "repair.use_cmd_vel_requested",
  title: "Publish to /cmd_vel_requested instead of /cmd_vel",
  rationale: "Only the safety supervisor is allowed to publish to /cmd_vel ...",
  hint: "publisher = node.create_publisher(Twist, '/cmd_vel_requested', 10)"
}
```

## 2. Bundle statuses

| Status                     | Meaning                                                |
|----------------------------|--------------------------------------------------------|
| `suggestion_only`          | safe to copy; operator may edit + retry                |
| `not_applicable`           | candidate is clean; nothing to repair                  |
| `requires_human_review`    | rejection reason cannot be auto-repaired; reviewer must inspect |

## 3. Suggestion catalogue

| Code                              | Trigger                                        |
|-----------------------------------|------------------------------------------------|
| `repair.use_cmd_vel_requested`    | publishes `/cmd_vel` directly                  |
| `repair.append_stop_command`      | no final zero-Twist publish                    |
| `repair.add_bounded_timeout`      | no bounded duration / deadline                 |
| `repair.bound_loop`               | `while True:` / `while 1:`                     |
| `escalate.shell_or_code_execution`| sanitizer flagged shell or eval                |
| `escalate.network_access`         | sanitizer flagged network I/O                  |
| `escalate.safety_override`        | sanitizer flagged supervisor override          |
| `escalate.destructive_command`    | sanitizer flagged destructive shell command    |

## 4. Honesty rules

- **No suggestion is ever auto-applied.** The bundle is metadata.
- A "fix" recorded here MAY be unsafe in another context; the
  hint is illustrative.
- Categorical escalations (shell / network / safety-override /
  destructive) always set `requires_human_review`.
- The catalogue is exhaustively tested in
  `test_repair_suggests_*` and
  `test_repair_escalates_human_review_for_unsafe_categories`.

## 5. Frontend behaviour

The frontend does NOT render an "apply" button for repair
suggestions. It displays each suggestion verbatim with the
`status` chip so the reviewer can copy the hint into their own
edit.

## 6. Related docs

- `docs/LOCAL_LLM_INTELLIGENCE_UPGRADE.md`
- `docs/LLM_CANDIDATE_RANKING_MODEL.md`
- `docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md`
