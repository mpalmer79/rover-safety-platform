import type { ArtifactRegistryFile } from "@/adapters/types";
import { cn } from "@/lib/utils";

interface DeterministicHashChainProps {
  files: readonly ArtifactRegistryFile[];
  className?: string;
}

function shortHash(hash: string): string {
  if (!hash) return "—";
  return hash.slice(0, 16);
}

/**
 * Human-readable list of an artefact's registered files plus their
 * sha256 prefixes. Surfaces the "deterministic" guarantee in a
 * single panel; the operator can compare these prefixes against
 * the on-disk bytes by running ``tools/hydrate_replay_artifacts.py
 * --check-only``.
 */
export function DeterministicHashChain({
  files,
  className,
}: DeterministicHashChainProps) {
  if (files.length === 0) {
    return (
      <p className={cn("body-mono text-base-500", className)}>
        No registered files for this artefact.
      </p>
    );
  }
  return (
    <table
      data-testid="deterministic-hash-chain"
      className={cn(
        "w-full border-separate border-spacing-0 text-[11px] font-mono",
        className,
      )}
    >
      <thead>
        <tr className="text-left text-base-500">
          <th className="pb-1 pr-3 font-normal">file</th>
          <th className="pb-1 pr-3 font-normal">sha256 (16)</th>
          <th className="pb-1 text-right font-normal">size</th>
        </tr>
      </thead>
      <tbody>
        {files.map((f) => (
          <tr key={f.relative_path} className="text-base-700">
            <td className="border-t border-base-200 py-1 pr-3 align-top">
              <span className="text-base-800">{f.relative_path}</span>
              {f.description ? (
                <span className="ml-1 text-base-500">· {f.description}</span>
              ) : null}
            </td>
            <td className="border-t border-base-200 py-1 pr-3 align-top text-base-600">
              {shortHash(f.expected_hash)}
            </td>
            <td className="border-t border-base-200 py-1 text-right align-top text-base-500">
              {f.size_bytes.toLocaleString()} B
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
