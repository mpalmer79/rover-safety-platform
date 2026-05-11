"use client";

import { useEffect, useId, useRef, useState } from "react";

interface MermaidViewProps {
  source: string;
  className?: string;
}

/**
 * Render Mermaid diagram source on the client. Mermaid pulls in
 * a large bundle; loading it dynamically keeps the static surface
 * small and avoids SSR pitfalls. The fallback (and the only thing
 * rendered server-side) is the raw source inside a ``<pre>`` so the
 * audit's deterministic text is always visible.
 */
export function MermaidView({ source, className }: MermaidViewProps) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, "_");
  const ref = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function render() {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          themeVariables: {
            background: "#11141b",
            primaryColor: "#1d2230",
            primaryTextColor: "#d2d6df",
            primaryBorderColor: "#3a4256",
            lineColor: "#525c75",
            secondaryColor: "#1b3d3a",
            tertiaryColor: "#161a23",
          },
        });
        const result = await mermaid.render(`mermaid-${id}`, source);
        if (!cancelled) {
          setSvg(result.svg);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    }
    render();
    return () => {
      cancelled = true;
    };
  }, [source, id]);

  if (svg) {
    return (
      <div
        ref={ref}
        className={className}
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    );
  }

  return (
    <pre
      className={`whitespace-pre rounded bg-base-100 p-3 font-mono text-xs text-base-700 ${className ?? ""}`}
      aria-label="Mermaid diagram source"
    >
      {error ? `// mermaid render error: ${error}\n` : ""}
      {source}
    </pre>
  );
}
