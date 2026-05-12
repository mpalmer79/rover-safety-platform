"use client";

import { typography } from "@/design-system/typography";
import type { SpatialReplayArtifact } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface PoseTracePanelProps {
  artifact: SpatialReplayArtifact | null;
  /** Optional limit on rendered samples. */
  limit?: number;
}

export function PoseTracePanel({ artifact, limit = 6 }: PoseTracePanelProps) {
  return (
    <TelemetryPanelFrame
      kicker="Pose trace"
      title={artifact?.scenario_id ?? "no spatial artefact"}
      derivation={artifact?.derivation_source ?? "—"}
      integrity={
        artifact?.validation_status === "passed"
          ? "passed"
          : artifact?.validation_status === "failed"
            ? "rejected"
            : "partial"
      }
    >
      {artifact ? (
        <div className="space-y-2">
          <p className={typography("caption")}>
            {artifact.sample_count} samples · {artifact.segment_count} segment(s)
            · {artifact.topic_sources.join(", ") || "no topics"}
          </p>
          {artifact.note ? (
            <p className={typography("bodyDense")}>{artifact.note}</p>
          ) : null}
          <table className="w-full text-[11px]">
            <thead className="text-[color:var(--mc-text-muted)]">
              <tr>
                <th className="text-left font-medium">t (ns)</th>
                <th className="text-left font-medium">x</th>
                <th className="text-left font-medium">y</th>
                <th className="text-left font-medium">θ</th>
                <th className="text-left font-medium">conf</th>
              </tr>
            </thead>
            <tbody>
              {artifact.samples.slice(0, limit).map((s) => (
                <tr key={s.sample_id}>
                  <td className="font-mono">{s.time_ns}</td>
                  <td className="font-mono">{s.x_m.toFixed(3)}</td>
                  <td className="font-mono">{s.y_m.toFixed(3)}</td>
                  <td className="font-mono">{s.theta_rad.toFixed(3)}</td>
                  <td className="font-mono">{s.confidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className={typography("bodyDense")}>
          No spatial-replay artefact for this mission.
        </p>
      )}
    </TelemetryPanelFrame>
  );
}
