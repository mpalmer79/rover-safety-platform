"use client";

import { typography } from "@/design-system/typography";
import { cn } from "@/lib/utils";
import type { SpatialReplayArtifact } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface TopicAvailabilityPanelProps {
  artifact: SpatialReplayArtifact | null;
}

export function TopicAvailabilityPanel({ artifact }: TopicAvailabilityPanelProps) {
  return (
    <TelemetryPanelFrame
      kicker="Topic availability"
      title={artifact ? `${artifact.topic_sources.length} present` : "no artifact"}
      derivation={artifact ? "spatial_replay.topic_sources" : "—"}
      integrity={
        artifact && artifact.missing_topics.length === 0 ? "passed" : "partial"
      }
    >
      {artifact ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Group title="present" topics={artifact.topic_sources} tone="ok" />
          <Group title="missing" topics={artifact.missing_topics} tone="warn" />
        </div>
      ) : (
        <p className={typography("bodyDense")}>
          Topic availability requires a spatial-replay artifact.
        </p>
      )}
    </TelemetryPanelFrame>
  );
}

function Group({
  title,
  topics,
  tone,
}: {
  title: string;
  topics: readonly string[];
  tone: "ok" | "warn";
}) {
  return (
    <div>
      <p className={typography("label")}>{title}</p>
      <ul className="mt-1 flex flex-wrap gap-1">
        {topics.length === 0 ? (
          <li className={typography("caption")}>none</li>
        ) : (
          topics.map((t) => (
            <li
              key={t}
              className={cn(
                "rounded-sm border px-1.5 py-0.5 font-mono text-[11px]",
                tone === "ok"
                  ? "border-[color:var(--mc-status-completed)] text-[color:var(--mc-status-completed)]"
                  : "border-[color:var(--mc-status-warning)] text-[color:var(--mc-status-warning)]",
              )}
            >
              {t}
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
