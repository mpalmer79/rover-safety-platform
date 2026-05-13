"use client";

import { useEffect, useId, useRef, useState } from "react";

interface MermaidViewProps {
  source: string;
  className?: string;
}

/**
 * Render Mermaid diagram source on the client.
 *
 * Mermaid pulls in a large bundle, so the loader stays dynamic — the
 * fallback rendered server-side is the raw source inside a ``<pre>``
 * (the audit's deterministic text is therefore always visible, even
 * if the client renderer never runs).
 *
 * Layout stability:
 *   - Both the SSR ``<pre>`` and the rendered SVG render inside the
 *     same wrapper ``<div>``, so React's hydration boundary does not
 *     swap the element type out from under the page layout.
 *   - The wrapper carries ``data-mermaid-state`` so tests + observers
 *     can wait for "rendered" before measuring layout.
 *   - ``contain: layout`` isolates the diagram's height changes from
 *     surrounding flow; the catalog's full-page screenshot is more
 *     stable as a result.
 *
 * Trust boundary (#10):
 *   The SVG injected via ``dangerouslySetInnerHTML`` below is produced
 *   by Mermaid from ``source``. Mermaid escapes node labels, but that
 *   is **not** a sandbox — rendering attacker-controlled Mermaid
 *   source would still be unsafe (SVG embeds ``<foreignObject>``,
 *   ``<script>``, event handlers, etc.). The ingested Mermaid source
 *   MUST come from checked-in repository files only (audits,
 *   traceability graphs, etc.). Never wire this component to an
 *   external feed, a database column, or a query parameter without
 *   sanitising upstream and routing through a server-side allow-list.
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
