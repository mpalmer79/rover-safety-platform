import { Hash } from "lucide-react";

import { cn } from "@/lib/utils";
import { shortHash } from "@/lib/utils";

interface DeterministicHashDisplayProps {
  label: string;
  hash: string | null | undefined;
  className?: string;
}

/**
 * Renders a deterministic SHA-256 prefix that ties an artefact to
 * its inputs. The full hash is available as a tooltip; the short
 * form keeps console rows readable.
 */
export function DeterministicHashDisplay({
  label,
  hash,
  className,
}: DeterministicHashDisplayProps) {
  return (
    <span
      title={hash ?? "no hash"}
      className={cn(
        "inline-flex items-center gap-1.5 rounded border border-base-200 bg-base-100 px-2 py-0.5 font-mono text-[11px] text-base-700",
        className,
      )}
    >
      <Hash aria-hidden className="h-3 w-3 text-base-500" />
      <span className="label">{label}</span>
      <span>{shortHash(hash, 16)}</span>
    </span>
  );
}
