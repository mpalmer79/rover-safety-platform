/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Disable telemetry; the operator UI never phones home.
  experimental: {},
  // Force a small, static export-friendly footprint. The app reads
  // JSON artefacts from the repository's evidence directories via
  // server components only — no API routes, no external fetches.
  poweredByHeader: false,
};

export default nextConfig;
