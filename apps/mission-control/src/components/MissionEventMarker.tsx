import { cn } from "@/lib/utils";

const SEVERITY_COLOUR: Record<string, string> = {
  info: "bg-base-400",
  warning: "bg-status-pending",
  rejection: "bg-status-rejected",
};

interface MissionEventMarkerProps {
  severity: string;
  label: string;
  className?: string;
}

/** Inline legend swatch for the mission map. */
export function MissionEventMarker({
  severity,
  label,
  className,
}: MissionEventMarkerProps) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-[11px]", className)}>
      <span
        aria-hidden
        className={cn(
          "inline-block h-2.5 w-2.5 rounded-full",
          SEVERITY_COLOUR[severity] ?? "bg-base-400",
        )}
      />
      <span className="text-base-700">{label}</span>
    </span>
  );
}
