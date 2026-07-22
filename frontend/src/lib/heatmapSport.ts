/**
 * Training-heatmap sport-filter contract.
 *
 * The single source of truth for the sport-filter values the heatmap control
 * emits and how they map onto the backend request. Every non-"all" value is
 * sent VERBATIM as the `sport` query param of GET /api/athletes/me/heatmap, so
 * it MUST be one of the values the backend's `_matches_sport` recognizes
 * ("ride" / "run"). Using the Strava activity_type strings ("riding" /
 * "running") here matches neither branch and falls through to "match every
 * activity", silently disabling the filter — the bug this module exists to
 * prevent from recurring.
 */

import type { HeatmapSport } from "@/types";

/** Sport-filter options for the heatmap control, in display order. */
export const HEATMAP_SPORTS: readonly [HeatmapSport, string][] = [
  ["all", "Tous"],
  ["ride", "Vélo"],
  ["run", "Course"],
];

/**
 * Translate a heatmap sport selection into the backend `sport` query param.
 * "all" aggregates every sport and is sent as *no* filter (undefined). Any
 * other value passes through unchanged because HeatmapSport's non-"all" values
 * are exactly the backend query-param values.
 */
export function heatmapSportParam(sport: HeatmapSport): string | undefined {
  return sport === "all" ? undefined : sport;
}
