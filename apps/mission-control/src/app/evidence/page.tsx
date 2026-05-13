import { loadTraceability } from "@/adapters/loader";
import { Panel } from "@/components/Panel";
import { RequirementBadge } from "@/components/RequirementBadge";
import { StatusPill } from "@/components/StatusPill";
import { formatTimestamp } from "@/lib/utils";
import { PageSurface } from "@/components/PageSurface";

export const dynamic = "force-static";

export default async function EvidencePage() {
  const traceability = await loadTraceability();

  return (
    <PageSurface>
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="label">Evidence & audit explorer</p>
        <h1 className="display-1">Traceability matrix</h1>
        <p className="text-base-700">
          ProjectBoundary&apos;s public claims are traceable to
          requirements, tests, and committed artifacts. The matrix
          below is rendered verbatim from the deterministic
          traceability artifact — every row points at architecture
          references, implementation files, scenarios, tests, and
          evidence on disk.
        </p>
      </header>

      <Panel eyebrow="What this proves" title="Reviewer summary">
        <ul className="space-y-1.5 text-sm text-base-700">
          <li>• Each requirement links to the architecture, code, and tests that satisfy it.</li>
          <li>• Status comes from the traceability run, not from this UI.</li>
          <li>• If a row would lie, the build fails — the artifact is regenerated and committed deterministically.</li>
        </ul>
      </Panel>

      <Panel
        eyebrow="Status"
        title={traceability?.overall_status ?? "not_evaluated"}
        trailing={
          traceability ? (
            <span className="text-xs text-base-500">
              generated {formatTimestamp(traceability.generated_at_utc)} ·{" "}
              {traceability.row_count} rows
            </span>
          ) : null
        }
      >
        {traceability ? (
          <p className="text-sm text-base-700">
            {traceability.row_count} requirements across{" "}
            {new Set(traceability.rows.map((r) => r.kind)).size} kinds.
          </p>
        ) : (
          <p className="body-mono">No traceability artifact on disk.</p>
        )}
      </Panel>

      {traceability ? (
        <Panel
          eyebrow="By requirement kind"
          title="Coverage"
        >
          <div className="space-y-4">
            {Array.from(new Set(traceability.rows.map((r) => r.kind))).sort().map((kind) => {
              const rows = traceability.rows.filter((r) => r.kind === kind);
              return (
                <details key={kind} className="rounded border border-base-200 bg-base-100">
                  <summary className="flex cursor-pointer items-baseline justify-between gap-2 px-3 py-2 text-sm">
                    <span className="font-mono text-base-900">{kind}</span>
                    <span className="text-xs text-base-500">{rows.length} requirements</span>
                  </summary>
                  <div className="space-y-2 border-t border-base-200 px-3 py-3">
                    {rows.map((row) => (
                      <article
                        key={row.req_id}
                        className="rounded border border-base-300 bg-base-50 p-3"
                      >
                        <header className="flex items-center justify-between gap-2">
                          <RequirementBadge reqId={row.req_id} status={row.status} />
                          <StatusPill
                            label={row.status_detail || row.status}
                            tone={
                              row.status === "passed"
                                ? "completed"
                                : row.status === "failed"
                                ? "rejected"
                                : "pending"
                            }
                          />
                        </header>
                        <h3 className="mt-2 text-sm font-medium text-base-900">
                          {row.title}
                        </h3>
                        {row.test_refs.length > 0 ? (
                          <p className="mt-1 font-mono text-xs text-base-600">
                            {row.test_refs.length} test bindings
                          </p>
                        ) : null}
                      </article>
                    ))}
                  </div>
                </details>
              );
            })}
          </div>
        </Panel>
      ) : null}

      <Panel eyebrow="Honesty rules" title="What this page enforces">
        <ul className="space-y-1.5 text-sm text-base-700">
          <li>• Every value comes from a committed JSON artifact.</li>
          <li>• No requirement is hidden — failed and not-executed
            requirements remain visible.</li>
          <li>• Rejected missions are not silently re-labelled.</li>
          <li>• Bag-backed claims require a real bag manifest;
            simulated rehearsals always carry the simulated chip.</li>
        </ul>
      </Panel>
    </div>
    </PageSurface>
  );
}
