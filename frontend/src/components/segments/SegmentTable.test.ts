import { describe, it, expect } from "bun:test";
import { sortSegments } from "./SegmentTable";
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
