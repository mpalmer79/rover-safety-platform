# Operator Experience Guidelines (Phase 17B)

The platform is **not safety-certified.** This page records the
small set of UX rules the mission-control UI follows. The intent
is to make the operator console feel intentional, premium, and
systems-engineered without ever overstating the platform's
capability.

## 1. Tone

* **Honest before slick.** Every surface preserves the deterministic
  backend's verbatim text. Status pills never re-code rejections,
  evidence chips never invert bag-backed claims.
* **Calm before flashy.** Single muted teal accent; risk + status
  colours are reserved for the data they describe. No glow, no
  neon, no rainbow gradient.
* **Mono before sans.** Hashes, requirement ids, event ids, and
  forbidden topics are mono-typeset so an operator can scan them
  fast.

## 2. Spacing + density

* 14 rem sidebar; remaining viewport for the route + panels.
* Panel padding: `px-4 py-3` for headers; `px-4 py-4` for body.
* Dense tables (`text-[11px]` mono) where a reviewer wants to scan
  numbers; `text-sm` body copy elsewhere.

## 3. Animation

Conserved to three styles:

1. The Phase 17A `CodeCard` staged fade-in.
2. The `MissionStateStepper` current-step `animate-pulse`.
3. The map scrubber's CSS-native range transition; no JS animation.

No looping background animations, no fake telemetry tickers, no
gimmicky typing animations.

## 4. Placeholders for unavailable data

Every panel that depends on optional audit fields renders an
explicit placeholder when the field is absent:

| Panel                          | Placeholder text                                                |
|--------------------------------|-----------------------------------------------------------------|
| `MissionMap`                   | "Spatial data unavailable for this mission."                    |
| `WaypointOverlay`              | "Select a waypoint on the map to see its bounded inputs."       |
| `RouteProgressIndicator`       | "No waypoints recorded for this rehearsal."                     |
| `SupervisorInterventionOverlay`| "No supervisor interventions recorded for this rehearsal."     |
| `SafetyZoneLayer`              | "No mission plan; safety zones unavailable."                    |
| `ReplayScrubber`               | "No rehearsal events recorded."                                 |
| `ReplayTimeline`               | "No rehearsal events recorded."                                 |
| `ReplayAnalyticsPanel`         | "No analytics artefact for this rehearsal."                     |

The empty case is always a complete sentence; the operator never
sees a blank panel.

## 5. Why Rejected? drilldown

Every rejected mission gets a `WhyRejectedDrilldown` panel at the
top of the detail page. The panel pairs the verbatim failure reason
with:

* an English explainer (one paragraph, no jargon);
* the verbatim validator and supervisor rejection codes;
* a list of related `REQ-*` ids so a reviewer can trace the rule
  back to the registry.

## 6. Mission proposal workbench

The workbench routes a request through the deterministic backend
artefacts. The screen surfaces:

* the mission library (accepted + rejected piles, both visible);
* a code-card grid that renders the verbatim Phase 15A skill
  output;
* the `MissionPlaybackPanel` on the per-mission detail page once a
  mission is opened.

## 7. Banners, footers, and disclaimers

* `SafetyBoundaryBanner` pinned to the top of every page.
* Sidebar footer: "Simulation-only. Not safety-certified.
  Bag-backed evidence count remains 0."
* Every spatial figure carries a caption with its data origin.
* Every audit panel carries the verbatim Phase 16 disclaimer.

If a future change attempts to suppress any of these, the Phase
17B honesty tests + the static-export grep in
`mission-control-ci.yml` reject the build.

## 8. Accessibility

* Every SVG has a `role="img"` and `aria-label`.
* Every interactive control has an explicit label.
* Status colours are paired with text labels so the UI doesn't
  rely on hue alone.
* The Mermaid renderer falls back to a `<pre>` source block when
  JavaScript is disabled.

## 9. What this guideline does not authorise

* No "live" CTA — no button labelled "deploy", "ship", or "send to
  robot".
* No metric labelled "live runtime maturity established" unless
  the Phase 13 maturity baseline says so.
* No bag-backed visual treatment unless the audit JSON declares it.
* No tile or panel that implies real-world operations data.
