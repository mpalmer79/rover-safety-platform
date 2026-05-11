# Autonomy Visualization Guide (Phase 17A)

The platform is **not safety-certified.** This guide records the
design rationale behind each component in
`apps/mission-control/src/components/`. Every component is built to
preserve the deterministic backend's honesty contract — the UI must
never be more optimistic than the artefact on disk.

## Visual language

* **Palette.** Slate base (`base.0..900`), muted teal accent
  (`accent.DEFAULT`), four risk colours, four status colours.
* **Typography.** `Inter` for prose; `JetBrains Mono` for hashes,
  status pills, requirement ids, and per-event timeline rows.
* **Motion.** Framer Motion is used only on the code card, where a
  short staged fade-in hints at the order a reader should scan the
  snippet (imports → constants → publisher setup → bounded loop →
  stop command → safety explanation).
* **Density.** Operator console proportions: 14 rem sidebar, dense
  panels, generous monospaced labels.

## Component-by-component rationale

### `SafetyBoundaryBanner`

Pinned at the top of every page. The banner repeats two facts: the
platform is not safety-certified, and the runtime safety supervisor
plus motion arbitration remain authoritative. It exists so a
reviewer landing on any screen sees the boundary immediately.

### `SiteNav`

Five primary destinations plus an honesty footer that repeats:
*"Simulation-only. Not safety-certified. Bag-backed evidence count
remains 0."*

### `Panel`

The reusable chrome around every console widget. Forces a consistent
eyebrow (kicker label) + title + trailing slot so every section
looks like it came from the same operations dashboard.

### `StatusPill`

Compact status badge. The pill never re-codes its input label —
"completed" stays "completed", "rejected" stays "rejected". Tones
are derived from the label when not explicit.

### `RiskBandBadge`

Risk band display: `low`, `guarded`, `restricted`, `blocked`.
Unknown bands fall back to `guarded` colouring so an unfamiliar
value never silently reads as low risk.

### `EvidenceStatusChip`

Renders two facts side-by-side: `evidence: <status>` and
`bag-backed: yes|no`. The component cannot fabricate a bag-backed
claim — the chip's text would contradict itself.

### `DeterministicHashDisplay`

Inline label + short hash + full hash in tooltip. Used wherever
the audit records a SHA-256 prefix (plan, runtime, replay, per-event).
The reviewer can confirm reproducibility by hovering.

### `MissionStateStepper`

Visual stepper for the rehearsal state machine: `created → validated
→ approved → rehearsing → completed`. Rejected and aborted statuses
recolour the stepper but never hide the halt point.

### `MissionCard`

Compact card for the dashboard and replay viewer. Surfaces the
status pill, risk band, evidence chip, plan + runtime hashes, and
the generated timestamp. Wraps a `Link` to the mission detail page
so the entire card is the clickable target.

### `ReplayTimeline`

Vertical event timeline. Each row preserves the verbatim severity
and deterministic hash from the audit bundle. Severities colour the
left rule (`info`, `warning`, `rejection`) so a reviewer cannot
miss a rejection event.

### `CodeCard`

The "wow factor" code panel on the Workbench. Renders the verbatim
Phase 15A skill code byte-for-byte. Lines fade in with a 10 ms
delay per row (capped at 600 ms total) — deliberate, not gimmicky.
Reading order is taken from the skill's `code_card.animation_steps`
payload so the audit and the UI agree.

### `CompilerDecisionCard`

Surface the Phase 14A / 16 validator diagnostics. Counts are
aggregated (info / warning / rejection) and every rejection is
listed verbatim. The card's left border is green on accept and red
on rejection.

### `SupervisorAuthorityPanel`

Renders the supervisor decision verbatim: status, safety status,
rationale, rejected reasons, allowed topics, forbidden topics, and
whether human review is required. The forbidden topic list is
rendered in red so a reviewer cannot miss a `/cmd_vel` block.

### `GovernanceHealthPanel`

Dashboard widget that aggregates completed / rejected / aborted
counts across every committed rehearsal plus the requirement count
from the traceability artefact. Always-explicit: "Bag-backed
evidence: 0".

### `AuditPanel`

Right-rail evidence summary on the mission detail page. Shows
generated-at, final status, safety status, failure reason,
deterministic hashes, evidence chip, and the disclaimer.

### `RequirementBadge`

Compact requirement-status badge for the evidence explorer and the
dashboard's requirement spot check. Tone is derived from
`passed | partial | failed | not_executed | skipped`.

### `ReplayAnalyticsPanel`

Per-rehearsal analytics card. Renders the integer counters from
the Phase 16 analytics bridge: rehearsals, approved, rejected,
aborted, completed, supervisor/validator rejections, deterministic
replay stable flag. No probabilistic data — no AI-derived metric.

### `MermaidView`

Client-side Mermaid renderer. The server-side fallback is the raw
Mermaid source inside a `<pre>` block so the diagram is always
readable, even when JavaScript is disabled.

## Conservative animations

The UI uses three animation styles only:

1. The code card's staged fade-in (`CodeCard`).
2. The current-step pulse on `MissionStateStepper` (`animate-pulse`).
3. The `fade-in` Tailwind keyframe applied via utility classes when
   a page mounts.

No glow effects, no rainbow gradients, no fake telemetry tickers.
