import { cn } from "@/lib/utils";

const TONE_CLASSES: Record<string, string> = {
  simulated: "border-status-pending/40 bg-status-pending/10 text-status-pending",
  static_only: "border-base-400 bg-base-200 text-base-700",
  not_evaluated: "border-base-400 bg-base-100 text-base-600",
  bag_backed: "border-status-completed/40 bg-status-completed/10 text-status-completed",
};

interface EvidenceStatusChipProps {
  status: string;
  bagBacked: boolean;
  className?: string;
}

/**
 * Communicates evidence origin honestly.
 *
 * The chip's text always shows the verbatim ``evidence_status`` from
 * the source artifact AND a separate ``bag-backed: yes|no`` label.
 * The UI cannot fabricate a bag-backed claim — the chip would
 * contradict itself.
 */
export function EvidenceStatusChip({
  status,
  bagBacked,
  className,
}: EvidenceStatusChipProps) {
  const tone = bagBacked
    ? TONE_CLASSES.bag_backed
    : TONE_CLASSES[status] ?? TONE_CLASSES.not_evaluated;
  return (
    <span
      title={`Evidence status: ${status}; bag-backed: ${bagBacked ? "yes" : "no"}`}
      className={cn(
        "inline-flex items-center gap-2 rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest",
        tone,
        className,
      )}
    >
      <span>evidence: {status}</span>
      <span aria-hidden>•</span>
      <span>bag-backed: {bagBacked ? "yes" : "no"}</span>
    </span>
  );
}
