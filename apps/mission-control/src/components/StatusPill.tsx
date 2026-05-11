import { cn } from "@/lib/utils";

type ToneKey =
  | "completed"
  | "pending"
  | "rejected"
  | "aborted"
  | "info"
  | "warning"
  | "rejection";

const TONE_CLASSES: Record<ToneKey, string> = {
  completed: "bg-status-completed/15 text-status-completed",
  pending: "bg-status-pending/15 text-status-pending",
  rejected: "bg-status-rejected/15 text-status-rejected",
  aborted: "bg-status-aborted/15 text-status-aborted",
  info: "bg-accent/15 text-accent",
  warning: "bg-status-pending/15 text-status-pending",
  rejection: "bg-status-rejected/15 text-status-rejected",
};

interface StatusPillProps {
  label: string;
  tone?: ToneKey;
  title?: string;
}

/** Compact status badge. The pill never re-codes the input label. */
export function StatusPill({ label, tone, title }: StatusPillProps) {
  const resolved: ToneKey =
    tone ??
    (label === "completed"
      ? "completed"
      : label === "rejected"
      ? "rejected"
      : label === "aborted"
      ? "aborted"
      : "pending");
  return (
    <span
      title={title ?? label}
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[11px] uppercase tracking-wider",
        TONE_CLASSES[resolved],
      )}
    >
      {label}
    </span>
  );
}
