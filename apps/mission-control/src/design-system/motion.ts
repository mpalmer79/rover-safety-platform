/**
 * Phase 20 motion + animation timing tokens.
 *
 * Animations must feel intentional. Components MUST consume one of
 * these presets rather than hand-coding durations.
 */

export type MotionKey =
  | "panelEnter"
  | "panelExit"
  | "focusEase"
  | "scrubber"
  | "hoverLift"
  | "stepIn";

export interface MotionToken {
  duration: number;
  ease: number[] | string;
}

export const MOTION: Record<MotionKey, MotionToken> = {
  panelEnter: { duration: 0.32, ease: [0.16, 0.84, 0.32, 1] },
  panelExit: { duration: 0.22, ease: [0.4, 0, 0.6, 1] },
  focusEase: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  scrubber: { duration: 0.18, ease: "easeOut" },
  hoverLift: { duration: 0.18, ease: "easeOut" },
  stepIn: { duration: 0.28, ease: [0.16, 0.84, 0.32, 1] },
};

export function motionPreset(key: MotionKey): MotionToken {
  return MOTION[key];
}

/**
 * Framer Motion variants for panel entrance. Components import this
 * and apply via ``initial="hidden" animate="visible"`` so that
 * panel choreography stays uniform.
 */
export const PANEL_VARIANTS = {
  hidden: { opacity: 0, y: 6 },
  visible: {
    opacity: 1,
    y: 0,
    transition: MOTION.panelEnter,
  },
};

export const STEP_VARIANTS = {
  hidden: { opacity: 0, x: 12 },
  visible: { opacity: 1, x: 0, transition: MOTION.stepIn },
};
