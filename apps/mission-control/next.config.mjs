import bundleAnalyzer from "@next/bundle-analyzer";

/**
 * Mission Control Next.js config.
 *
 * The bundle analyser is wired behind ANALYZE=true so a developer
 * can inspect per-route JS payload composition without affecting
 * normal CI builds:
 *
 *   ANALYZE=true npm run build
 *
 * The analyzer writes an HTML report under .next/analyze/ which is
 * uploaded as a workflow artifact when CI runs the bundle-budget
 * job with ANALYZE=true.
 */
const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === "true",
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Disable telemetry; the operator UI never phones home.
  experimental: {},
  // Force a small, static export-friendly footprint. The app reads
  // JSON artifacts from the repository's evidence directories via
  // server components only — no API routes, no external fetches.
  poweredByHeader: false,
};

export default withBundleAnalyzer(nextConfig);
