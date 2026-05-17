/**
 * Catalog fixtures for MissionRouteGlyph.
 */

import type { ComponentProps } from "react";

import { MissionRouteGlyph } from "@/components/MissionRouteGlyph";
import { FIX_AUDIT } from "./_shared";

type Props = ComponentProps<typeof MissionRouteGlyph>;

export const STATES: Record<string, Props> = {
  rejected: { audit: FIX_AUDIT } as Props,
};
