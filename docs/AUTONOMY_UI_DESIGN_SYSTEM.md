# Autonomy UI Design System (Phase 18 → 19)

The platform is **not safety-certified.** This document records
the visual + interaction language the operator console uses so
that future panels stay coherent.

**Phase 19 supersedes this document for the token + theme layer.**
See `docs/MISSION_CONTROL_DESIGN_SYSTEM.md` for the canonical
off-black / off-white token system, gradient surface rules, and
responsive layout primitives. This document is preserved as the
Phase 18 reference for downstream callers that still hard-code
Tailwind utility classes.

## 1. Palette

```
base       slate ramp (0..900)         neutral chrome
accent     muted teal (#3cb4a8)        single authority signal
accent-soft #1b3d3a                    accent fill / soft glow
risk-low    #4ade80                    bounded inputs accepted
risk-guarded #facc15                   warning band
risk-restricted #fb923c                restricted band
risk-blocked #f87171                   rejected band
status-completed #4ade80               final success
status-pending   #facc15               waiting / partial
status-warning   #fb923c    (Phase 18 NEW)   bag-backed degraded
status-rejected  #f87171               rejected
status-aborted   #a78bfa               aborted
```

Use accent only for the single most authoritative element on a
panel. Use risk colours only for the data they describe. Avoid
neon, avoid gradients, avoid sci-fi imagery.

## 2. Typography

- Display 1 — `text-3xl font-semibold tracking-tight` (page H1).
- Display 2 — `text-xl font-semibold tracking-tight` (panel
  titles).
- Label — `text-[11px] uppercase tracking-[0.14em] text-base-500`
  (eyebrows + chip text).
- Body mono — `font-mono text-sm leading-relaxed text-base-700`
  (deterministic content: hashes, IDs, topics, timestamps).
- Body — default sans. Use sparingly; prefer mono for evidence.

## 3. Panel system

```
.panel              standard surface (rounded, border, soft shadow)
.panel-tight        light border + slight rounding (timeline rows)
.panel-elevated     thicker shadow + brighter border (immersive)
.glass-panel        translucent + backdrop-blur (overlays only)
```

Use `.glass-panel` only when an overlay sits over the immersive
scene; never use it for general layout.

## 4. Motion

- The scrubber and the camera mode tabs are the only interactive
  surfaces that change scene state.
- `framer-motion` is used sparingly for the existing CodeCard and
  the SpatialReplayBadge — never for the immersive scene itself.
- Camera transitions are deterministic snaps; there is no easing.
- No element animates continuously; the dashboard is calm.

## 5. Iconography

- `lucide-react` for every icon.
- Icons should be 16-18 px and inherit the surrounding text colour.
- The status pill keeps its `●` glyph; the badges keep `◆`.

## 6. Spacing

- Page padding: `px-6 py-6`.
- Section spacing: `space-y-6` between primary sections,
  `space-y-4` inside columns.
- Panel headers: `px-4 py-3`. Panel bodies: `px-4 py-4`.
- Dense tables: `text-[11px]` mono with `border-spacing-0`.

## 7. Honesty in design

- Captions never re-code data. Status pills, evidence chips, and
  the new `SpatialReplayBadge` render the verbatim string from the
  adapter.
- An empty / missing artefact is rendered as an explicit placeholder
  ("No artefact registered…", "Spatial data unavailable.") — never
  as a blank panel.
- A "warning" colour signals a real warning the operator must
  understand, not aesthetic flourish.
