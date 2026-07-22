import { describe, it, expect, afterEach } from "bun:test";
import { HEATMAP_SPORTS, heatmapSportParam } from "./heatmapSport";
import { athletes } from "./api";
import type { HeatmapSport } from "@/types";

/**
 * Regression guard for the silent heatmap sport-filter no-op: the control used
 * to emit the Strava activity_type strings "riding"/"running", which the
 * backend's _matches_sport does NOT recognize (it accepts only "ride"/"run"),
 * so every non-"all" selection fell through to "match every activity" and both
 * "Vélo" and "Course" rendered identical all-sport heatmaps. These tests pin
 * the UI-value -> backend query-param contract end to end.
 */

// Values the backend GET /api/athletes/me/heatmap `sport` query param accepts
// (mirrors _matches_sport in backend/app/api/routes/athletes.py).
const BACKEND_SPORT_VALUES = ["ride", "run"] as const;

describe("HEATMAP_SPORTS", () => {
  it("labels the three filter options in display order", () => {
    expect(HEATMAP_SPORTS.map(([, label]) => label)).toEqual([
      "Tous",
      "Vélo",
      "Course",
    ]);
  });

  it("emits only backend-recognized sport values (never the activity_type strings)", () => {
    const nonAll = HEATMAP_SPORTS.map(([value]) => value).filter(
      (v) => v !== "all"
    );
    // The exact values _matches_sport recognizes — not "riding"/"running".
    expect(nonAll).toEqual([...BACKEND_SPORT_VALUES]);
    expect(nonAll).not.toContain("riding");
    expect(nonAll).not.toContain("running");
  });
});

describe("heatmapSportParam", () => {
  it("maps 'all' to no filter (undefined) and passes other values through", () => {
    expect(heatmapSportParam("all")).toBeUndefined();
    expect(heatmapSportParam("ride")).toBe("ride");
    expect(heatmapSportParam("run")).toBe("run");
  });
});

describe("athletes.getHeatmap wire format", () => {
  const originalFetch = globalThis.fetch;
  let lastUrl = "";

  const installFetchSpy = () => {
    lastUrl = "";
    globalThis.fetch = ((input: string | URL | Request) => {
      lastUrl = typeof input === "string" ? input : input.toString();
      return Promise.resolve({
        ok: true,
        headers: { get: () => null },
        json: async () => ({ points: [], activity_count: 0 }),
      } as unknown as Response);
    }) as typeof fetch;
  };

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("sends each control option through to the exact backend sport param", async () => {
    for (const [value] of HEATMAP_SPORTS) {
      installFetchSpy();
      const param = heatmapSportParam(value as HeatmapSport);
      await athletes.getHeatmap(param ? { sport: param } : undefined);

      const query = new URL(lastUrl).searchParams.get("sport");
      if (value === "all") {
        expect(query).toBeNull(); // aggregate-all: no filter on the wire
      } else {
        expect(query).toBe(value); // "Vélo" -> ride, "Course" -> run
        expect(BACKEND_SPORT_VALUES).toContain(query as "ride" | "run");
      }
      // The old bug leaked activity_type strings onto the wire; never again.
      expect(lastUrl).not.toContain("sport=riding");
      expect(lastUrl).not.toContain("sport=running");
    }
  });
});
