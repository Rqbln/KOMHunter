import { describe, it, expect } from "bun:test";
import {
  sortSegments,
  filterSegments,
  segmentsToCsv,
  difficultyLabel,
} from "./SegmentTable";
import type { SegmentSummary } from "@/types";

/** Build a minimal SegmentSummary, overriding only the fields under test. */
function seg(partial: Partial<SegmentSummary> & { id: number }): SegmentSummary {
  return {
    name: `seg-${partial.id}`,
    distance: 1000,
    avg_grade: 5,
    elev_difference: 50,
    start_latlng: [0, 0],
    end_latlng: [0, 0],
    climb_category: 0,
    difficulty_score: 50,
    ...partial,
  };
}

describe("sortSegments — terrain columns", () => {
  it("sorts by distance ascending and descending", () => {
    const segments = [
      seg({ id: 1, distance: 3000 }),
      seg({ id: 2, distance: 1000 }),
      seg({ id: 3, distance: 2000 }),
    ];

    expect(sortSegments(segments, "distance", "asc").map((s) => s.id)).toEqual([
      2, 3, 1,
    ]);
    expect(sortSegments(segments, "distance", "desc").map((s) => s.id)).toEqual([
      1, 3, 2,
    ]);
  });

  it("sorts by name case-insensitively", () => {
    const segments = [
      seg({ id: 1, name: "banana" }),
      seg({ id: 2, name: "Apple" }),
      seg({ id: 3, name: "cherry" }),
    ];
    expect(sortSegments(segments, "name", "asc").map((s) => s.id)).toEqual([
      2, 1, 3,
    ]);
  });

  it("does not mutate the input array", () => {
    const segments = [seg({ id: 1, distance: 2 }), seg({ id: 2, distance: 1 })];
    const before = segments.map((s) => s.id);
    sortSegments(segments, "distance", "asc");
    expect(segments.map((s) => s.id)).toEqual(before);
  });
});

describe("sortSegments — enrichment columns (null sorts last)", () => {
  it("orders by popularity (prestige_score) with missing values last, both directions", () => {
    const segments = [
      seg({ id: 1, prestige_score: 40 }),
      seg({ id: 2, prestige_score: null }),
      seg({ id: 3, prestige_score: 90 }),
      seg({ id: 4 }), // prestige_score undefined
    ];

    // desc = most famous first; both null and undefined go last.
    const desc = sortSegments(segments, "popularity", "desc").map((s) => s.id);
    expect(desc.slice(0, 2)).toEqual([3, 1]);
    expect(desc.slice(2).sort()).toEqual([2, 4]);

    // asc must ALSO push the missing ones last (not first).
    const asc = sortSegments(segments, "popularity", "asc").map((s) => s.id);
    expect(asc.slice(0, 2)).toEqual([1, 3]);
    expect(asc.slice(2).sort()).toEqual([2, 4]);
  });

  it("orders by competitiveness ascending (slowest KOM = easiest first), missing last", () => {
    const segments = [
      seg({ id: 1, competitiveness_score: 80 }),
      seg({ id: 2, competitiveness_score: 20 }),
      seg({ id: 3 }), // missing
      seg({ id: 4, competitiveness_score: 50 }),
    ];
    expect(
      sortSegments(segments, "competitiveness", "asc").map((s) => s.id)
    ).toEqual([2, 4, 1, 3]);
  });
});

describe("filterSegments — client-side display filters", () => {
  it("hides suspicious-KOM rows only when hideSuspicious is on", () => {
    const segments = [
      seg({ id: 1, kom_suspicious: true }),
      seg({ id: 2, kom_suspicious: false }),
      seg({ id: 3, kom_suspicious: null }),
      seg({ id: 4 }), // undefined
    ];
    expect(
      filterSegments(segments, {
        hideSuspicious: false,
        minDifficulty: 0,
      }).map((s) => s.id)
    ).toEqual([1, 2, 3, 4]);
    expect(
      filterSegments(segments, {
        hideSuspicious: true,
        minDifficulty: 0,
      }).map((s) => s.id)
    ).toEqual([2, 3, 4]);
  });

  it("drops rows below the minimum difficulty threshold", () => {
    const segments = [
      seg({ id: 1, difficulty_score: 10 }),
      seg({ id: 2, difficulty_score: 50 }),
      seg({ id: 3, difficulty_score: 90 }),
    ];
    expect(
      filterSegments(segments, {
        hideSuspicious: false,
        minDifficulty: 50,
      }).map((s) => s.id)
    ).toEqual([2, 3]);
  });

  it("does not mutate the input array", () => {
    const segments = [seg({ id: 1, difficulty_score: 10 })];
    const before = segments.map((s) => s.id);
    filterSegments(segments, { hideSuspicious: true, minDifficulty: 100 });
    expect(segments.map((s) => s.id)).toEqual(before);
  });
});

describe("difficultyLabel", () => {
  it("buckets scores into Easy/Moderate/Hard/Expert", () => {
    expect(difficultyLabel(0)).toBe("Easy");
    expect(difficultyLabel(24)).toBe("Easy");
    expect(difficultyLabel(25)).toBe("Moderate");
    expect(difficultyLabel(49)).toBe("Moderate");
    expect(difficultyLabel(50)).toBe("Hard");
    expect(difficultyLabel(74)).toBe("Hard");
    expect(difficultyLabel(75)).toBe("Expert");
    expect(difficultyLabel(100)).toBe("Expert");
  });
});

describe("segmentsToCsv", () => {
  it("emits a header row and the requested columns with a Strava URL", () => {
    const csv = segmentsToCsv([
      seg({
        id: 42,
        name: "Col Test",
        distance: 2500,
        avg_grade: 7.25,
        difficulty_score: 80,
        prestige_score: 60,
        competitiveness_score: 30,
        kom_time: "5:00",
      }),
    ]);
    const lines = csv.split("\r\n");
    expect(lines[0]).toBe(
      "name,distance_km,avg_grade,difficulty_score,category,prestige_score,competitiveness_score,kom_time,strava_url"
    );
    expect(lines[1]).toBe(
      "Col Test,2.50,7.3,80,Expert,60,30,5:00,https://www.strava.com/segments/42"
    );
  });

  it("leaves enrichment cells blank when absent and quotes commas", () => {
    const csv = segmentsToCsv([
      seg({ id: 7, name: "Foo, Bar", distance: 1000, difficulty_score: 10 }),
    ]);
    const line = csv.split("\r\n")[1];
    // Name with a comma is quoted; missing prestige/competitiveness/kom blank.
    expect(line).toBe(
      '"Foo, Bar",1.00,5.0,10,Easy,,,,https://www.strava.com/segments/7'
    );
  });
});
