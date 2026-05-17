"use client";

import { useEffect, useId, useRef, useState } from "react";

interface MermaidViewProps {
  source: string;
  className?: string;
}

/**
 * Renders Mermaid source on the client; SSR fallback is a `<pre>` of the raw source.
 *
 * Trust boundary (#10): `source` MUST come from checked-in repo files only.
 * The injected SVG is not sandboxed - attacker-controlled Mermaid is unsafe.
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

  const state = svg ? "rendered" : error ? "error" : "pending";

  return (
    <div
      ref={ref}
      data-testid="mermaid-view"
      data-mermaid-state={state}
      className={className}
      style={{ contain: "layout" }}
    >
      {svg ? (
        // Trust boundary (#10): `source` MUST come from checked-in
        // repository files only — see the component docstring above.
        // eslint-disable-next-line react/no-danger
        <div dangerouslySetInnerHTML={{ __html: svg }} />
      ) : (
        <pre
          className="whitespace-pre rounded bg-base-100 p-3 font-mono text-xs text-base-700"
          aria-label="Mermaid diagram source"
        >
          {error ? `// mermaid render error: ${error}\n` : ""}
          {source}
        </pre>
      )}
    </div>
  );
}
