# ADR-007: Design Token Discipline (off-black / off-white, no raw hex)

## Status

Accepted

## Context

The Mission Control workspace ships a light + dark theme via CSS
variables. Without a typed token system, two failure modes appear:

1. **Generic-AI aesthetic.** A surface rendered with the default
   Tailwind `bg-black`/`bg-white`/`text-black`/`text-white`
   classes reads as untuned and visually identical to dozens of
   open-source dashboards. This undermines the platform's
   credibility as a reviewer-facing artifact.
2. **WCAG contrast violations.** Pure black + pure white surfaces
   produce overshooting contrast (≈ 21:1) that fatigues a reader
   and clashes with the muted-accent + status-colour palette the
   rest of the UI uses.

The honesty discipline that governs the rest of the platform
applies here too: design choices should be **named** and
**enforced**, not ambient.

## Decision

A typed token module at
`apps/mission-control/src/styles/tokens.ts` is the single source
of truth for every colour. The matching CSS file
`apps/mission-control/src/styles/theme.css` declares one CSS
variable per token under `:root, html.dark` and the contrasting
set under `html.light`.

Hard rules, enforced by
`apps/mission-control/tests/design-tokens.test.ts`:

- **No pure black** anywhere. The darkest dark-mode surface is
  `--mc-bg-2: #0c1018` (off-black graphite).
- **No pure white** anywhere. The brightest light-mode surface is
  `--mc-surface-elevated: #fdfefe` (warm off-white).
- **No raw `#000` / `#fff`** hex outside `tokens.ts` /
  `theme.css`.
- **No `bg-black`, `bg-white`, `text-black`, `text-white`**
  Tailwind class anywhere under `src/`.
- Components import the named token (`var(--mc-surface)`,
  `tokenSet().accent`) instead of hard-coding hex.

Gradients exist only where they add **depth**, not where they add
**decoration**. The `GradientPanel` component is the single
surface that emits gradients; ad-hoc `bg-[linear-gradient(...)]`
elsewhere fails review.

## Consequences

### Positive

- The light + dark themes both render at AA contrast on every
  surface; no surface hits the >20:1 ratio of pure black-on-white.
- A reviewer can read the token file as the design system; no
  hidden Tailwind utility carries semantic meaning.
- The visual regression suite locks two states per page (light +
  dark); a token change that breaks contrast surfaces as a
  baseline diff immediately.
- The honesty test prevents a future "just add white here"
  shortcut.

### Negative

- New colours require a token addition and a corresponding test
  update; ad-hoc styling is impossible.
- Components must consume `var(--mc-*)` via Tailwind's
  `bg-[var(--mc-surface)]` syntax, which is verbose.
- Some third-party components (Mermaid, lucide icons) need
  per-call colour overrides that wrap the token.

### Operational

- The honesty test runs as part of the standard vitest suite; no
  separate linter is needed.
- The Item 1 coverage gate has per-file floors for safety-
  relevant components; the design-token test sits outside
  coverage and is purely a static rule.

## References

- `apps/mission-control/src/styles/tokens.ts`
- `apps/mission-control/src/styles/theme.css`
- `apps/mission-control/tests/design-tokens.test.ts`
- `apps/mission-control/src/components/GradientPanel.tsx`
- `apps/mission-control/README.md` (light/dark + accessibility
  sections)
- ADR-006 — the static export means tokens are baked at build
  time; no runtime theme injection
