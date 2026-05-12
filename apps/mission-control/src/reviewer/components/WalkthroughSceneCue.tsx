"use client";

import { Camera } from "lucide-react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { SceneCue } from "@/3d/orchestration/sceneCueModel";

interface WalkthroughSceneCueProps {
  cue: SceneCue;
  className?: string;
}

export function WalkthroughSceneCue({ cue, className }: WalkthroughSceneCueProps) {
  return (
    <section
      data-testid="walkthrough-scene-cue"
      data-cue-kind={cue.kind}
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <header className="inline-flex items-center gap-1.5 text-[color:var(--mc-accent)]">
        <Camera aria-hidden className="h-4 w-4" />
        <span className={typography("label")}>Scene cue · {cue.kind}</span>
      </header>
      <dl className="grid grid-cols-1 gap-x-3 gap-y-1 text-[12px] sm:grid-cols-2">
        <Row label="camera_mode" value={cue.cameraMode} />
        <Row label="focus_target" value={cue.focusTarget ?? "—"} />
        <Row label="focus_ref" value={cue.focusRef ?? "—"} />
        <Row label="rationale" value={cue.rationale} />
      </dl>
    </section>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <dt className={typography("label")}>{label}</dt>
      <dd className="font-mono text-[12px] text-[color:var(--mc-text)] break-all">
        {value}
      </dd>
    </div>
  );
}
