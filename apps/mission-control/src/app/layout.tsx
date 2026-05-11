import type { Metadata } from "next";
import type { ReactNode } from "react";

import { ResponsiveShell } from "@/components/ResponsiveShell";
import { SafetyBoundaryBanner } from "@/components/SafetyBoundaryBanner";
import { ThemeProvider, THEME_BOOTSTRAP_SCRIPT } from "@/lib/theme-provider";

import "@/styles/theme.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mission Control · Rover Safety Platform",
  description:
    "Simulation-only mission control UI for the deterministic autonomy " +
    "validation and safety orchestration platform.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        {/* No-FOUC theme bootstrap. Resolves stored / system preference
            BEFORE the page paints so light mode never flashes harsh
            black, and dark mode never flashes harsh white. */}
        <script
          dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP_SCRIPT }}
        />
      </head>
      <body className="min-h-dvh text-[color:var(--mc-text)]">
        <ThemeProvider>
          <SafetyBoundaryBanner />
          <ResponsiveShell>{children}</ResponsiveShell>
        </ThemeProvider>
      </body>
    </html>
  );
}
