import { cn } from "@/lib/utils";

interface WarehouseLaneMapProps {
  className?: string;
}

/**
 * Decorative warehouse-lane background used on the dashboard.
 *
 * This is a STATIC SVG — not real warehouse data. The component
 * exists to give the dashboard a familiar mission-control aesthetic
 * without implying that the platform knows about any specific
 * warehouse. The caption is explicit about the data origin.
 */
export function WarehouseLaneMap({ className }: WarehouseLaneMapProps) {
  return (
    <figure className={cn("panel-tight overflow-hidden", className)}>
      <svg
        role="img"
        aria-label="Decorative warehouse lane background"
        viewBox="0 0 480 200"
        width="100%"
        height="160"
      >
        <defs>
          <pattern
            id="warehouse-lanes"
            width="40"
            height="40"
            patternUnits="userSpaceOnUse"
          >
            <rect width="40" height="40" fill="#11141b" />
            <path d="M0 20H40" stroke="#1d2230" strokeWidth="0.6" />
            <path d="M20 0V40" stroke="#1d2230" strokeWidth="0.6" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#warehouse-lanes)" />
        {/* Lanes */}
        {Array.from({ length: 6 }).map((_, idx) => (
          <rect
            key={`lane-${idx}`}
            x={20 + idx * 78}
            y={20}
            width="60"
            height="160"
            fill="#161a23"
            stroke="#262c3c"
            strokeWidth="1"
          />
        ))}
        {/* Dock zone */}
        <rect
          x={20}
          y={180}
          width="440"
          height="12"
          fill="#1b3d3a"
          stroke="#3cb4a8"
          strokeWidth="1"
        />
        <text
          x={240}
          y={189}
          textAnchor="middle"
          fontSize="10"
          fill="#7c8499"
          fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
        >
          dock zone (illustrative)
        </text>
      </svg>
      <figcaption className="border-t border-base-200 px-3 py-2 text-[11px] text-base-500">
        <span className="label mr-2">background</span>
        Illustrative warehouse layout. No real-world coordinates,
        capacities, or routes implied.
      </figcaption>
    </figure>
  );
}
