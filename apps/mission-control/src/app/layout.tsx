import type { Metadata } from "next";
import type { ReactNode } from "react";

import { ResponsiveShell } from "@/components/ResponsiveShell";
import { SafetyBoundaryBanner } from "@/components/SafetyBoundaryBanner";
import { ThemeProvider, THEME_BOOTSTRAP_SCRIPT } from "@/lib/theme-provider";

import "@/styles/theme.css";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://projectboundary.vercel.app"),
  title: {
    default: "ProjectBoundary · Rover Safety Platform",
    template: "%s · ProjectBoundary",
  },
  description:
    "A simulation-only rover safety platform featuring a 3D warehouse mission replay, deterministic safety-boundary validation, supervisor intervention logic, and evidence-backed review artifacts.",
  openGraph: {
    title: "ProjectBoundary · Rover Safety Platform",
    description:
      "3D warehouse mission replay for autonomous safety validation, supervisor intervention, and evidence-backed review.",
    url: "https://projectboundary.vercel.app",
    siteName: "ProjectBoundary",
    images: [
      {
        url: "/opengraph-image.png",
        width: 1200,
        height: 627,
        alt: "ProjectBoundary rover safety platform showing a 3D warehouse mission replay and safety boundary validation.",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "ProjectBoundary · Rover Safety Platform",
    description:
      "3D warehouse mission replay for autonomous safety validation and evidence-backed review.",
    images: ["/opengraph-image.png"],
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-icon.png",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
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
