import Link from "next/link";

import { GradientPanel } from "@/components/GradientPanel";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";

export default function NotFound() {
  return (
    <PageSurface>
      <GradientPanel elevated className="px-4 py-4 sm:px-5 sm:py-5">
        <header className="space-y-1">
          <p className="label">Mission control</p>
          <h1 className="display-1">No artefact at this path</h1>
          <p className="text-muted text-sm sm:text-base">
            The platform did not commit a JSON artefact for this
            route. Static export resolves every route at build time;
            an unknown path indicates either a typo or a renamed
            artefact.
          </p>
        </header>
      </GradientPanel>
      <Panel
        eyebrow="Diagnostics"
        title="What to do"
        className="mt-6"
      >
        <ul
          data-testid="route-not-found"
          className="space-y-1 text-sm text-[color:var(--mc-text)]"
        >
          <li>
            • Confirm the path matches a committed artefact.
          </li>
          <li>
            • If you reached this from a link, the link is stale.
            Open an issue against the page you came from.
          </li>
          <li>
            •{" "}
            <Link className="underline" href="/">
              Return to the dashboard.
            </Link>
          </li>
        </ul>
      </Panel>
    </PageSurface>
  );
}
