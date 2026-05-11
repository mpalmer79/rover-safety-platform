import { CheckCircle2, AlertCircle, XCircle } from "lucide-react";

import type { ValidationDiagnostic } from "@/adapters/types";
import { summariseDiagnostics } from "@/adapters/loader";
import { cn } from "@/lib/utils";

interface CompilerDecisionCardProps {
  diagnostics: readonly ValidationDiagnostic[];
  className?: string;
}

/**
 * Surfaces validator diagnostics produced by the deterministic
 * compile/validate pipeline. The card aggregates counts and lists
 * every rejection in detail so the operator can see exactly which
 * rule fired.
 */
export function CompilerDecisionCard({ diagnostics, className }: CompilerDecisionCardProps) {
  const counts = summariseDiagnostics(diagnostics);
  const rejected = diagnostics.filter((d) => d.severity === "rejection");
  const warnings = diagnostics.filter((d) => d.severity === "warning");
  const accepted = counts.rejection === 0;

  return (
    <section
      className={cn(
        "panel",
        accepted ? "border-status-completed/30" : "border-status-rejected/30",
        className,
      )}
    >
      <header className="flex items-center gap-3 border-b border-base-200 px-4 py-3">
        {accepted ? (
          <CheckCircle2 aria-hidden className="h-5 w-5 text-status-completed" />
        ) : (
          <XCircle aria-hidden className="h-5 w-5 text-status-rejected" />
        )}
        <div className="space-y-0.5">
          <p className="label">Validator decision</p>
          <h2 className="display-2">{accepted ? "Accepted" : "Rejected"}</h2>
        </div>
        <div className="ml-auto flex gap-2 text-xs">
          <span className="rounded bg-base-200 px-2 py-0.5 font-mono text-base-700">
            info {counts.info}
          </span>
          <span className="rounded bg-status-pending/15 px-2 py-0.5 font-mono text-status-pending">
            warn {counts.warning}
          </span>
          <span className="rounded bg-status-rejected/15 px-2 py-0.5 font-mono text-status-rejected">
            rej {counts.rejection}
          </span>
        </div>
      </header>
      <div className="space-y-3 px-4 py-4 text-sm">
        {rejected.length > 0 ? (
          <div>
            <p className="label mb-1.5">Rejections</p>
            <ul className="space-y-1.5">
              {rejected.map((d, idx) => (
                <li key={`r-${idx}`} className="flex items-start gap-2 text-status-rejected">
                  <XCircle aria-hidden className="mt-0.5 h-3.5 w-3.5" />
                  <span>
                    <span className="font-mono text-xs">{d.code}</span>
                    <span className="text-base-800"> — {d.message}</span>
                    {d.parameter ? (
                      <span className="text-base-500"> ({d.parameter})</span>
                    ) : null}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {warnings.length > 0 ? (
          <div>
            <p className="label mb-1.5">Warnings</p>
            <ul className="space-y-1.5">
              {warnings.map((d, idx) => (
                <li key={`w-${idx}`} className="flex items-start gap-2 text-status-pending">
                  <AlertCircle aria-hidden className="mt-0.5 h-3.5 w-3.5" />
                  <span>
                    <span className="font-mono text-xs">{d.code}</span>
                    <span className="text-base-800"> — {d.message}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {accepted && rejected.length === 0 && warnings.length === 0 ? (
          <p className="body-mono">All deterministic validator checks passed.</p>
        ) : null}
      </div>
    </section>
  );
}
