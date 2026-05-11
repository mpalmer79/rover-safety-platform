import { cn } from "@/lib/utils";

const TONE_CLASSES: Record<string, string> = {
  passed: "border-status-completed/40 bg-status-completed/10 text-status-completed",
  partial: "border-status-pending/40 bg-status-pending/10 text-status-pending",
  not_executed: "border-base-400 bg-base-100 text-base-600",
  failed: "border-status-rejected/40 bg-status-rejected/10 text-status-rejected",
  skipped: "border-base-400 bg-base-100 text-base-600",
};

interface RequirementBadgeProps {
  reqId: string;
  status: string;
  title?: string;
  className?: string;
}

export function RequirementBadge({ reqId, status, title, className }: RequirementBadgeProps) {
  const tone = TONE_CLASSES[status] ?? TONE_CLASSES.not_executed;
  return (
    <span
      title={title ?? `${reqId}: ${status}`}
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-widest",
        tone,
        className,
      )}
    >
      <span>{reqId}</span>
      <span aria-hidden>•</span>
      <span>{status}</span>
    </span>
  );
}
