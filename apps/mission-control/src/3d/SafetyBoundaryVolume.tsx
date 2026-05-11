"use client";

import { BoxGeometry, EdgesGeometry } from "three";
import { useMemo } from "react";

/**
 * Safety-boundary volume.
 *
 * Renders a translucent outline around the active mission area.
 * The volume is illustrative; it conveys "the supervisor authority
 * lives outside this volume" rather than any specific keepout.
 */

interface SafetyBoundaryVolumeProps {
  size?: number;
  color?: string;
}

export function SafetyBoundaryVolume({
  size = 6,
  color = "#facc15",
}: SafetyBoundaryVolumeProps) {
  const edges = useMemo(
    () => new EdgesGeometry(new BoxGeometry(size * 2, 0.8, size * 2)),
    [size],
  );
  return (
    <lineSegments geometry={edges} position={[0, 0.4, 0]}>
      <lineBasicMaterial color={color} transparent opacity={0.45} />
    </lineSegments>
  );
}
