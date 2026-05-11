# Mission Control Design System (Phase 19)

The platform is **not safety-certified.** This document defines the
single visual language used across the Mission Control UI.

## 1. Hard rules

1. **No solid black backgrounds.** Dark mode resolves to an off-black
   graphite (`#10141c` family).
2. **No solid white backgrounds.** Light mode resolves to a warm
   off-white (`#f6f8fb` family).
3. **No harsh contrast.** Text colour never lands on a pure
   complement; the contrast ratio is WCAG AA on every surface.
4. **No neon cyberpunk styling.** Accent is a single muted teal in
   each theme; status colours are reserved for the data they describe.
5. **Mobile, tablet, and desktop are all first-class.** Every page is
   built on `PageSurface` + `ResponsiveGrid`.

## 2. Token surfaces

```
tokens.ts ── TOKENS, CSS_VAR, tokenSet(), ThemeName
theme.css ── --mc-bg-0 / --mc-surface / --mc-text / ... (light + dark)
```

The CSS variables are the single source of truth at runtime.
Components consume them via `bg-[var(--mc-surface)]` or directly in
component CSS classes. No component re-declares a hex value.

### Off-black / off-white palette

| Token              | Dark           | Light          |
|--------------------|----------------|----------------|
| `--mc-bg-0`        | `#10141c`      | `#f6f8fb`      |
| `--mc-bg-1`        | `#0e1320`      | `#eef1f7`      |
| `--mc-bg-2`        | `#0c1018`      | `#e7ecf3`      |
| `--mc-surface`     | `#161b26`      | `#fbfcfe`      |
| `--mc-border`      | `#262d3e`      | `#d6dbe6`      |
| `--mc-text`        | `#dbe0ec`      | `#1f2937`      |
| `--mc-accent`      | `#5dd6c4`      | `#1d8f86`      |

## 3. Component primitives

- `PageSurface` — every route's outermost wrapper. Caps width at
  `max-w-7xl`, applies mobile-first padding, and renders the body
  on the layered gradient backdrop.
- `ResponsiveShell` — desktop sidebar / mobile drawer with the
  `Phase 19` brand + primary navigation. Mobile mode reveals a
  hamburger menu below `md`.
- `ResponsiveGrid` — three shapes (`stack`, `auto`, `mission`)
  cover every layout we use today.
- `GradientPanel` — four tones (`default`, `accent`, `warning`,
  `rejected`). The single panel surface across the UI.
- `ThemeToggle` — medium-sized switch on the home page; small
  switch elsewhere.

## 4. Gradient system

Backgrounds are layered: a radial accent + a vertical bg-stack
gradient, both expressed as `var(--mc-*)` references so the
mapping switches with the theme. Panel gradients use
`color-mix()` to blend accent into the neutral panel surface for
the `accent` / `warning` / `rejected` tones.

## 5. Typography

| Class       | Use                                            |
|-------------|------------------------------------------------|
| `.display-1`| Page H1 (`text-3xl`, `font-semibold`)          |
| `.display-2`| Panel title (`text-xl`, `font-semibold`)       |
| `.label`    | Eyebrow / muted caption (`text-[11px]`, mono)  |
| `.body-mono`| Deterministic content (hashes, IDs, topics)    |

## 6. Iconography + motion

- `lucide-react` icons everywhere.
- Theme transitions are 220 ms ease. No motion in the immersive
  scene beyond user-driven scrubber + mode tabs.
- `framer-motion` remains scoped to the existing Phase 17A code
  card.

## 7. Honesty rules baked into the design system

- The `design-tokens.test.ts` honesty grep scans `src/` for
  `bg-black` / `bg-white` / `text-black` / `text-white` and raw
  `#000` / `#fff` hex values. Tokens may declare canonical values;
  everything else must reference them.
- Theme transitions never flash pure black/white during load
  (validated by the `theme.test.tsx` "load" assertion).
- The Safety boundary banner is rendered above the responsive
  shell so it never gets pushed off-screen.

See `docs/THEME_AND_RESPONSIVE_UI.md` for theme + responsive
specifics, and `docs/AUTONOMY_UI_DESIGN_SYSTEM.md` for the
underlying Phase 18 design language this layer extends.
