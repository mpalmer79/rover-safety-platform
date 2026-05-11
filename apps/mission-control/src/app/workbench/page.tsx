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
          Pick a canonical request to see how the deterministic
          pipeline routes it. The workbench surfaces the sanitizer
          decision, validator outcome, supervisor authority, and the
          generated copyable code — every value is taken verbatim
          from the committed audit bundles.
        </p>
      </header>

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
          Phase 15A workbench emitted. No autoformat, no re-flow —
          the deterministic hash in the audit depends on this exact
          text.
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
