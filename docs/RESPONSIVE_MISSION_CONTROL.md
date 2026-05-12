# Responsive Mission Control

> Mobile, tablet, desktop, ultrawide — one operator console.

## Breakpoints

Mission Control follows Tailwind's responsive scale:

| Token  | Min width  | Use                                                 |
| ------ | ---------- | --------------------------------------------------- |
| (none) | 0          | Mobile · single-column stacked mission review.      |
| `sm`   | 640px      | Compact phones, narrow handheld tablets.            |
| `md`   | 768px      | Tablet portrait · 6-column grid + 12rem sidebar.    |
| `lg`   | 1024px     | Tablet landscape / small laptop · keeps the grid.   |
| `xl`   | 1280px     | Desktop · 14rem sidebar + 12-column grid.           |
| `2xl`  | 1536px     | Ultrawide · same grid, more generous max-width.     |

## Layout posture

* **Mobile** — sticky top bar (`workspace-mobile-bar`) with a drawer
  trigger. Panels collapse to one column. The 3D scene canvas
  remains constrained to the panel min-height; the page itself
  never overflows horizontally.
* **Tablet portrait** — persistent 12rem sidebar; panel grid drops
  to two columns (`md:grid-cols-6` with 6-column spans).
* **Tablet landscape + desktop** — 12-column grid using the
  preset's per-panel `colSpan`.
* **Ultrawide** — `max-w-7xl` cap on `PageSurface` keeps line
  length readable; the workspace shell does not cap, allowing
  panels to use the full grid.

## Drawer pattern

The mobile drawer is presentational: opening it never alters
workspace state. The `ResponsiveWorkspaceDrawer` component is
mounted only when the viewport collapses below `md`, and it always
re-uses the same `WorkspaceSidebar` as desktop — there is no
divergent mobile nav.

## Reduced motion

`html.theme-transition` honours `prefers-reduced-motion: reduce` —
the theme transition class is suppressed so colour shifts do not
animate. Framer Motion panel entrances use short, eased curves
(see `@/design-system/motion`) and degrade quietly under reduced
motion.

## Honesty rules

* No `bg-black` / `bg-white` / `text-black` / `text-white`.
* No raw `#000` / `#fff` hex outside `tokens.ts` + `theme.css`.
* No horizontal overflow on any tested breakpoint.
* No layout state persists across reloads — workspaces remain
  deterministic JSON presets.

`tests/responsive-layout.test.tsx` and `tests/design-tokens.test.ts`
encode the rules above.
