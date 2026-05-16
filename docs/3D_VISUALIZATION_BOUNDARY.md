# 3D Visualisation Boundary (Phase 18)

The platform is **not safety-certified.** This document records
the hard boundary the immersive scene must respect.

## 1. The boundary

The immersive scene is a **client-side, deterministic, evidence-
driven** view of committed replay artifacts. It is NOT:

- a digital twin;
- a simulator;
- a real-time telemetry view;
- a real-time control surface;
- a path planner;
- a SLAM viewer;
- a sensor fusion stack;
- a mission editor.

The scene reads. It does not write. It does not stream. It does
not connect to anything.

## 2. Forbidden imports

The honesty test grep
(`apps/mission-control/tests/hydration-honesty.test.tsx`) asserts
no file under `src/` imports any of:

- `socket.io-client`, `socket.io`
- `ws`, `engine.io-client`, `eventsource`
- `@stomp/stompjs`, `mqtt`

And no file under `src/3d/` imports any of:

- `rosbag2`
- `mcap`, `@mcap/core`, `@mcap/nodejs`

## 3. Forbidden language constructs

The honesty test grep also asserts:

- no `new WebSocket(...)` is constructed anywhere in `src/`;
- no `new EventSource(...)` is constructed anywhere in `src/`;
- no `setInterval(...)` is called anywhere in `src/`.

`setTimeout` is allowed because Next.js + Vitest call it
indirectly through their own runtimes; the test only forbids
explicit polling loops.

## 4. Forbidden behaviours

The scene must not:

- mutate replay artifacts at runtime;
- fabricate pose samples for a missing run;
- render a `bag-backed` badge for a fixture or bounded-input
  derivation;
- run an animation loop that is not driven by user interaction or
  scrubber position;
- load external 3D assets over the network.

## 5. Allowed surfaces

The scene may:

- read the spatial-replay artifact via the registry-aware loader;
- read rehearsal events directly from the audit JSON;
- compute deterministic geometry from those inputs;
- expose camera modes via React state;
- render WebGL inside `<Canvas>`;
- fall back to the Phase 17C 2D panel when WebGL is unavailable.

## 6. Why the boundary exists

The credibility of the platform's safety story rests on every
operator surface being honest about what it knows. Phase 18 makes
the operator console look like an autonomy operations centre; the
boundary in this document ensures that visual upgrade does not
imply runtime authority the platform does not have.
