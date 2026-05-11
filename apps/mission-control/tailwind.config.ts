import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "'Inter'",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "'Segoe UI'",
          "Roboto",
          "sans-serif",
        ],
        mono: [
          "'JetBrains Mono'",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
      colors: {
        // Operator-console palette: muted slate base, single
        // accent for authority callouts, status colours for risk.
        base: {
          0: "#0b0d12",   // chrome
          50: "#11141b",
          100: "#161a23",
          200: "#1d2230",
          300: "#262c3c",
          400: "#3a4256",
          500: "#525c75",
          600: "#7c8499",
          700: "#aab1c1",
          800: "#d2d6df",
          900: "#eef0f4",
        },
        accent: {
          // muted teal — calm authority signal, never a button
          DEFAULT: "#3cb4a8",
          soft: "#1b3d3a",
        },
        risk: {
          low: "#4ade80",
          guarded: "#facc15",
          restricted: "#fb923c",
          blocked: "#f87171",
        },
        status: {
          completed: "#4ade80",
          pending: "#facc15",
          rejected: "#f87171",
          aborted: "#a78bfa",
        },
      },
      boxShadow: {
        panel: "0 0 0 1px rgba(255,255,255,0.04), 0 1px 2px rgba(0,0,0,0.5)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(2px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 200ms ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
