"use client";

import { typography } from "@/design-system/typography";
import { cn } from "@/lib/utils";
import type { ArtifactRegistryRecord } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface EvidenceIntegrityPanelProps {
  records: readonly ArtifactRegistryRecord[];
}

export function EvidenceIntegrityPanel({ records }: EvidenceIntegrityPanelProps) {
  const passed = records.filter((r) => r.integrity === "passed").length;
  const partial = records.filter((r) => r.integrity === "partial").length;
  const rejected = records.filter((r) => r.integrity === "rejected").length;
  const bagBacked = records.filter((r) => r.derivation_source === "bag_backed").length;

  return (
    <TelemetryPanelFrame
      kicker="Evidence integrity"
      title={`${records.length} artifact${records.length === 1 ? "" : "s"}`}
      derivation="artifact_registry"
      integrity={rejected > 0 ? "rejected" : partial > 0 ? "partial" : "passed"}
    >
      <ul className="space-y-1.5 text-[12px]">
        <Row label="passed" value={passed} tone="passed" />
        <Row label="partial" value={partial} tone="partial" />
        <Row label="rejected" value={rejected} tone="rejected" />
        <Row label="bag_backed" value={bagBacked} tone={bagBacked > 0 ? "passed" : "warning"} />
      </ul>
      <p className={cn(typography("caption"), "mt-2")}>
        bag-backed evidence count is preserved verbatim from each
        registry record’s <code>derivation_source</code> field.
      </p>
    </TelemetryPanelFrame>
  );
}

function Row({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "passed" | "partial" | "rejected" | "warning";
}) {
  const color =
    tone === "passed"
      ? "var(--mc-status-completed)"
      : tone === "partial"
        ? "var(--mc-status-pending)"
        : tone === "rejected"
          ? "var(--mc-status-rejected)"
          : "var(--mc-status-warning)";
  return (
    <li className="flex items-center justify-between border-b border-[color:var(--mc-border)] py-1 last:border-none">
      <span className={typography("label")}>{label}</span>
      <span
        className="font-mono text-[12px]"
        style={{ color }}
      >
        {value}
      </span>
    </li>
  );
}
