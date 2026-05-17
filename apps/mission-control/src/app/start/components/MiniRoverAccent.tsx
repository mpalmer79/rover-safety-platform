"use client";

import { motion, useReducedMotion } from "framer-motion";

/**
 * Subtle robotics personality accent. Small, professional, never
 * the focal point. Renders a stylised top-down rover that drifts
 * slightly to suggest motion.
 */
export function MiniRoverAccent({ className = "" }: { className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.svg
      viewBox="0 0 64 64"
      className={className}
      aria-hidden
      animate={
        reduce
          ? undefined
          : { y: [0, -2.5, 0], rotate: [0, 1.5, 0] }
      }
      transition={{ duration: 4.4, repeat: Infinity, ease: "easeInOut" }}
    >
      <defs>
        <linearGradient id="rover-body" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3cb4a8" />
          <stop offset="100%" stopColor="#1f7a72" />
        </linearGradient>
      </defs>
      {/* sensor sweep */}
      {!reduce ? (
        <motion.circle
          cx={32}
          cy={32}
          r={22}
          fill="none"
          stroke="rgba(60,180,168,0.45)"
          strokeWidth={0.8}
          initial={{ r: 22, opacity: 0 }}
          animate={{ r: [22, 30, 22], opacity: [0.0, 0.55, 0.0] }}
          transition={{ duration: 2.4, repeat: Infinity, ease: "easeOut" }}
        />
      ) : null}
      {/* chassis */}
      <rect x="14" y="18" width="36" height="28" rx="5" fill="url(#rover-body)" />
      {/* lidar dome */}
      <circle cx="32" cy="22" r="3.5" fill="#0a0f1a" stroke="#5fe5d6" strokeWidth="0.6" />
      <circle cx="32" cy="22" r="1.2" fill="#5fe5d6" />
      {/* wheels */}
      <rect x="10" y="22" width="5" height="8" rx="1.2" fill="#0a0f1a" />
      <rect x="10" y="34" width="5" height="8" rx="1.2" fill="#0a0f1a" />
      <rect x="49" y="22" width="5" height="8" rx="1.2" fill="#0a0f1a" />
      <rect x="49" y="34" width="5" height="8" rx="1.2" fill="#0a0f1a" />
      {/* status LEDs */}
      <circle cx="22" cy="40" r="1.4" fill="#3cb4a8" />
      <circle cx="32" cy="40" r="1.4" fill="#facc15" />
      <circle cx="42" cy="40" r="1.4" fill="#5fb0ff" />
    </motion.svg>
  );
}
