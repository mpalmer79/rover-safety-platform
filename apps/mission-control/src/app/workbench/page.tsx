import Link from "next/link";

import {
  listMissionLibraryEntries,
  loadAcceptedSkills,
} from "@/adapters/loader";
import { CodeCard } from "@/components/CodeCard";
import { Panel } from "@/components/Panel";
import { StatusPill } from "@/components/StatusPill";
import { PageSurface } from "@/components/PageSurface";

export const dynamic = "force-static";

export default async function WorkbenchPage() {
  const [library, skills] = await Promise.all([
    listMissionLibraryEntries(),
    loadAcceptedSkills(),
  ]);

  const accepted = library.filter((e) => e.kind === "accepted");
  const rejected = library.filter((e) => e.kind === "rejected");

  return (
    <PageSurface>
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="label">Mission proposal workbench</p>
        <h1 className="display-1">Compose a deterministic mission</h1>
        <p className="text-base-700">
          The workbench shows how ProjectBoundary handles proposed
          missions and generated skill candidates. Accepted intents
          can proceed through validation. Rejected intents are blocked
          before they can affect motion. Every value comes verbatim
          from the committed audit bundles.
        </p>
      </header>

      <Panel eyebrow="What this proves" title="Reviewer summary">
        <ul className="space-y-1.5 text-sm text-base-700">
          <li>• Accepted intents flow through validator and supervisor checks before any simulated motion.</li>
          <li>• Rejected intents are blocked by the sanitizer or validator — they never reach motion authority.</li>
          <li>• Generated skill candidates are surfaced as data; they are never executed by this UI.</li>
        </ul>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <Panel
          eyebrow="Mission library"
          title="Accepted intents"
          trailing={<StatusPill label={`${accepted.length} accepted`} tone="completed" />}
        >
          <ul className="space-y-2">
            {accepted.map((entry) => (
              <li key={entry.example_id}>
                <Link
                  href={`/missions/${entry.mission_id}`}
                  className="block rounded border border-base-200 bg-base-100 px-3 py-2 transition-colors hover:border-accent/40"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-mono text-sm text-base-900">
                      {entry.example_id}
                    </span>
                    <span className="text-xs text-base-500">
                      {entry.waypoints.length} waypoints
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-base-600">{entry.description}</p>
                </Link>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel
          eyebrow="Mission library"
          title="Rejected intents"
          trailing={<StatusPill label={`${rejected.length} rejected`} tone="rejected" />}
        >
          <ul className="space-y-2">
            {rejected.map((entry) => (
              <li key={entry.example_id}>
                <Link
                  href={`/missions/${entry.mission_id}`}
                  className="block rounded border border-base-200 bg-base-100 px-3 py-2 transition-colors hover:border-status-rejected/40"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-mono text-sm text-base-900">
                      {entry.example_id}
                    </span>
                    <span className="text-xs text-status-rejected">rejected</span>
                  </div>
                  <p className="mt-1 text-xs text-base-600">{entry.description}</p>
                </Link>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <header className="space-y-1 pt-4">
        <p className="label">Skill authoring workbench</p>
        <h2 className="display-2">Generated code candidates</h2>
        <p className="text-base-700">
          Each card preserves the verbatim bytes the deterministic
          skill workbench emitted. No autoformat, no re-flow — the
          deterministic hash in the audit depends on this exact text.
        </p>
      </header>

      <div className="grid gap-4 xl:grid-cols-2">
        {skills.length === 0 ? (
          <Panel eyebrow="Skill library" title="No artefacts">
            <p className="body-mono">
              Regenerate with{" "}
              <code>rover_ws/tools/generate_skill_examples.py</code>.
            </p>
          </Panel>
        ) : (
          skills.slice(0, 4).map((skill) => (
            <CodeCard key={skill.skill_id} skill={skill} />
          ))
        )}
      </div>
    </div>
    </PageSurface>
  );
}
