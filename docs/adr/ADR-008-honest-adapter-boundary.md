# ADR-008: Honest Adapter Boundary (null on ENOENT, no fabrication)

## Status

Accepted

## Context

The Mission Control UI reads every artifact from committed JSON
on disk via `apps/mission-control/src/adapters/loader.ts`. Many
artifacts are optional: a rehearsal might not yet have a replay
review, a mission might not yet have a spatial-replay artifact,
the canonical registry might not yet list a run, the live-runtime
maturity report might be absent. A naive implementation would
either:

- crash the build on the first missing file (brittle), or
- silently fall back to a default-shaped object (dishonest).

The platform's no-fake-green rule applies here. The UI must show
**absence** when a file is absent; it must not invent the shape
of a missing audit.

## Decision

The adapter follows a deliberate three-rule contract:

1. **Return `null` on ENOENT.** Every `readJson`-style function
   catches `ENOENT` / `ENOTDIR` and returns `null`. The caller is
   responsible for rendering an honest placeholder
   (`<p>No artifact found for this run.</p>`).
2. **Throw on other errors.** A `JSON.parse` failure, a permission
   error, or any other `fs.readFile` failure propagates as a
   thrown error. Item 2 wired route-level `error.tsx` files to
   render these inside the standard `PageSurface` chrome with the
   route name, the error digest, and a Retry button — never the
   default Next.js error UI.
3. **Never fabricate.** No fallback object is created. If a
   missing field is present in the file but its value is empty,
   that's the answer — the adapter does not "fix" it.

Concretely:

```ts
async function readJson<T>(filePath: string): Promise<T | null> {
  try {
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw) as T;
  } catch (err) {
    const code = (err as NodeJS.ErrnoException).code;
    if (code === "ENOENT" || code === "ENOTDIR") return null;
    throw err;
  }
}
```

Every consumer (server component) handles the `null` branch
explicitly: the mission detail page renders "No spatial replay
artifact for this run" rather than an empty map; the dashboard
renders "No rehearsal audits found" with a regen command rather
than a fake placeholder card.

## Consequences

### Positive

- The honesty test in
  `apps/mission-control/tests/honesty.test.ts` can ban network
  imports because the adapter is the only I/O surface.
- The visual regression suite produces baselines for the
  null-data states; a future regression that silently masks a
  missing file appears as a baseline diff.
- The Item 2 `error.tsx` files have a clear semantic: ENOENT is
  expected and renders inline; everything else escalates to the
  route-level error boundary.
- The catalog at `/catalog` (Item 5) is required by the honesty
  test to include null-data fixtures for safety-relevant
  components — null-data is a first-class state, not an edge
  case.

### Negative

- Every consumer must render a null branch. There is no
  ergonomic shortcut.
- A consumer that forgets the null branch creates a React render
  failure rather than a visible "missing" UI; this is caught by
  the per-file coverage gate (`adapter.test.ts` exercises the
  null path for every loader function).

### Operational

- The adapter's exception surface is part of the build contract.
  Adding a new artifact type requires a matching loader function,
  a `null` return on missing, and a route-level renderer that
  handles the `null` branch.
- The Phase-18 hydration CLI
  (`tools/hydrate_replay_artifacts.py`) produces a clean working
  tree before the UI build runs; this is the operational
  guarantee that the build sees a consistent on-disk state.

## References

- `apps/mission-control/src/adapters/loader.ts`
- `apps/mission-control/src/adapters/paths.ts`
- `apps/mission-control/tests/adapter.test.ts`
- `apps/mission-control/tests/honesty.test.ts`
- `apps/mission-control/src/app/error.tsx` (Item 2 — non-ENOENT
  fallback)
- `apps/mission-control/src/app/not-found.tsx`
- ADR-006 — the static export means the adapter runs at build
  time; the null branch is rendered into the prerendered HTML
- ADR-007 — null-data states use the same tokens as data-present
  states so the layout never collapses
