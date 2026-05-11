# Theme & Responsive UI (Phase 19)

The platform is **not safety-certified.** This document explains the
theme switching behaviour and the responsive layout shell.

## 1. Theme switching

`apps/mission-control/src/lib/theme-provider.tsx` exports:

- `ThemeProvider` — wraps the app; resolves the stored or system
  theme on mount; persists every change to `localStorage`.
- `useTheme()` — returns `{ theme, setTheme, toggle, ready }`.
- `THEME_BOOTSTRAP_SCRIPT` — synchronous inline `<script>` that
  applies the resolved theme class to `<html>` BEFORE the page
  paints. This is what prevents a harsh black/white flash on load.

Storage key: `mc-theme-preference`.

Resolution order:
1. `localStorage.mc-theme-preference` if set.
2. `window.matchMedia("(prefers-color-scheme: light)").matches`
   → `light`, otherwise → `dark`.
3. `DEFAULT_THEME = "dark"`.

## 2. Toggle component

`ThemeToggle` is `role="switch"` with `aria-checked`, an
`aria-label` that names the next state, and a focus-visible ring
in the accent colour. The home page renders the medium-sized
variant; secondary surfaces use the compact variant.

## 3. Responsive layout

`ResponsiveShell` is the only layout shell. Three breakpoints:

| Width        | Layout                                            |
|--------------|----------------------------------------------------|
| `< md`       | top bar with hamburger; drawer slides in over body |
| `md`         | persistent 12 rem sidebar + scrollable main        |
| `lg`         | persistent 14 rem sidebar + scrollable main        |

The main column carries `min-w-0 overflow-y-auto` so wide
content (tables, immersive scene canvas, long event streams)
scrolls inside the column rather than overflowing the body.

`PageSurface` (every route's outermost wrapper) adds mobile-first
padding (`px-3 py-4`) and tablet/desktop step-ups (`sm:px-5
sm:py-5 lg:px-8 lg:py-7`), capped at `max-w-7xl`.

`ResponsiveGrid` exposes three shapes:

- `stack` → 1 column at every breakpoint.
- `auto` → 1 col mobile, 2 col `md`, 3 col `xl`.
- `mission` → 1 col mobile, 2 col `md`, the asymmetric mission
  detail shape (`1.4fr_1fr`) at `lg`.

## 4. Tests

- `tests/theme.test.tsx` — toggle behaviour, persistence,
  aria-label, keyboard activation, no harsh-colour flash.
- `tests/responsive-layout.test.tsx` — PageSurface padding,
  ResponsiveGrid shapes, GradientPanel tones, safety banner.
- `tests/design-tokens.test.ts` — token colours never resolve to
  pure black / pure white, no `bg-black`/`bg-white` etc. in src.

## 5. Honesty rules

- The toggle never overrides a stored preference silently; the
  user choice always wins.
- The bootstrap script reads only `localStorage` + `matchMedia` —
  it never makes a network call.
- The system preference fallback uses the canonical
  `prefers-color-scheme: light` query; happy-dom's defaults are
  stubbed in tests to keep behaviour deterministic.
- No theme transition flashes solid black/white. Both palettes
  resolve to off-black / off-white tokens.

## 6. Related docs

- `docs/MISSION_CONTROL_DESIGN_SYSTEM.md`
- `docs/AUTONOMY_UI_DESIGN_SYSTEM.md` (Phase 18)
- `docs/IMMERSIVE_MISSION_CONTROL.md` (Phase 18)
