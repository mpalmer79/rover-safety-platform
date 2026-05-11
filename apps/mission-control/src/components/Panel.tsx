import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface PanelProps {
  title?: ReactNode;
  eyebrow?: string;
  trailing?: ReactNode;
  className?: string;
  children: ReactNode;
}

/** Standard operator-console panel chrome. */
export function Panel({ title, eyebrow, trailing, className, children }: PanelProps) {
  return (
    <section className={cn("panel", className)}>
      {(title || eyebrow || trailing) && (
        <header className="flex items-baseline justify-between gap-3 border-b border-base-200 px-4 py-3">
          <div className="space-y-0.5">
            {eyebrow ? <p className="label">{eyebrow}</p> : null}
            {title ? <h2 className="display-2">{title}</h2> : null}
          </div>
          {trailing}
        </header>
      )}
      <div className="px-4 py-4">{children}</div>
    </section>
  );
}
