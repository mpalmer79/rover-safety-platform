"use client";

/**
 * Bridge between the existing 2D playback panel and the immersive
 * 3D scene. The bridge is a thin client wrapper that dynamic-imports
 * the heavy R3F module so SSR / static export do not pull three.js
 * into the prerendered HTML.
 *
 * The bridge accepts the same inputs as ``MissionPlaybackPanel`` and
 * delegates rendering to the 3D playback panel. When the immersive
 * scene fails to mount (e.g. WebGL unsupported) the bridge falls
 * back to the existing 2D panel — never to fabricated data.
 */

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { MissionPlaybackPanel } from "@/components/MissionPlaybackPanel";
import type { MissionPlan, RehearsalEvent, SpatialReplayArtifact } from "@/adapters/types";

const MissionPlayback3D = dynamic(
  () => import("./MissionPlayback3D").then((m) => m.MissionPlayback3D),
  { ssr: false, loading: () => <ImmersiveScenePlaceholder /> },
);

interface MissionTimelineBridgeProps {
  plan: MissionPlan | null;
  events: readonly RehearsalEvent[];
  spatialReplay: SpatialReplayArtifact | null;
  /** Force the 2D fallback (used by tests). */
  prefer2D?: boolean;
}

export function MissionTimelineBridge({
  plan,
  events,
  spatialReplay,
  prefer2D = false,
}: MissionTimelineBridgeProps) {
  const [webglSupported, setWebglSupported] = useState<boolean | null>(null);

  useEffect(() => {
    if (prefer2D || typeof window === "undefined") {
      setWebglSupported(false);
      return;
    }
    try {
      const canvas = document.createElement("canvas");
      const ctx =
        canvas.getContext("webgl2") || canvas.getContext("webgl");
      setWebglSupported(Boolean(ctx));
    } catch {
      setWebglSupported(false);
    }
  }, [prefer2D]);

  if (webglSupported === null) {
    return <ImmersiveScenePlaceholder />;
  }
  if (!webglSupported) {
    return (
      <MissionPlaybackPanel
        plan={plan}
        events={events}
        spatialReplay={spatialReplay}
      />
    );
  }
  return (
    <MissionPlayback3D
      plan={plan}
      events={events}
      spatialReplay={spatialReplay}
    />
  );
}

function ImmersiveScenePlaceholder() {
  return (
    <div
      data-testid="immersive-scene-placeholder"
      className="rounded border border-base-200 bg-base-100 px-4 py-6 text-sm text-base-500"
    >
      Loading immersive mission scene…
    </div>
  );
}
