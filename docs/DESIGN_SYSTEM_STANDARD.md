# Design System Standard

> The single source of truth for Mission Control surfaces.

## Modules

`apps/mission-control/src/design-system/` exports five token sets:

* `typography.ts` — eight named typography keys
  (`display`, `heading`, `subheading`, `body`, `bodyDense`,
  `mono`, `label`, `caption`).
* `spacing.ts` — three operator-density modes
  (`comfortable`, `standard`, `dense`) and a shared spacing scale.
* `motion.ts` — six named motion presets and panel / step Framer
  Motion variants.
* `gradients.ts` — semantic surface tokens
  (`panel`, `panelElevated`, `glass`, `hero`, `topbar`, `sidebar`,
  `telemetry`, `walkthrough`).
* `accessibility.ts` — `relativeLuminance`, `contrastRatio`,
  `meetsAA`, `meetsAALarge` helpers.

The combined token set sits on top of the Phase 19 colour tokens
in `@/styles/tokens` and `@/styles/theme.css`.

## Hard rules

* No pure black (`#000`, `#000000`, `black`) anywhere.
* No pure white (`#fff`, `#ffffff`, `white`) anywhere.
* No `bg-black`, `bg-white`, `text-black`, `text-white` classes.
* Components consume tokens via the helpers (`typography`,
  `surface`, `densitySpec`, `motionPreset`). Raw hex / inline
  duration values in components are a CI failure.

These rules are enforced by `tests/design-tokens.test.ts` and
`tests/design-system.test.ts`.

## Contrast verification

`tests/design-system.test.ts` asserts that:

* the off-black graphite + off-white pearl contrast (`#0d1117`
  against `#f6f8fb`) is greater than 15:1;
* body text passes WCAG AA against the panel surface in both
  themes;
* muted text passes the relaxed AA-large floor.

## Authoring a new component

1. Read the kicker / title / mono pattern in
   `components/telemetry/TelemetryPanelFrame.tsx`.
2. Import the typography + surface tokens — do NOT write raw
   class strings for sizes, weights, or gradient colors.
3. Add a fixture under
   `apps/mission-control/src/components/__fixtures__/<Name>.fixtures.ts`
   AND import the component in `tests/a11y.test.tsx`. The honesty
   test in `tests/honesty.test.ts` enforces both.
4. Run `npm run test:no-coverage`. The design + honesty tests
   double as your CI gate.
