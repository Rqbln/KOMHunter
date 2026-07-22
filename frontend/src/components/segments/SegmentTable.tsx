"use client";

/**
 * Segment table component for displaying discovered segments.
 *
 * Column headers (Name, Distance, Elevation, Grade, Difficulty) are sortable:
 * clicking a header sorts by that column and toggles asc/desc, with an arrow
 * indicator. Sorting is controlled locally so both the home and search pages
 * benefit without extra wiring.
 */

import { useMemo, useState } from "react";
import { SegmentRow } from "./SegmentRow";
import type { SegmentSummary } from "@/types";

interface SegmentTableProps {
  segments: SegmentSummary[];
  isLoading?: boolean;
  onSegmentClick: (segmentId: number) => void;
}

type SortKey = "name" | "distance" | "elevation" | "grade" | "difficulty";
type SortDirection = "asc" | "desc";

/** Extract the comparable value for a given sort column. */
function sortValue(segment: SegmentSummary, key: SortKey): number | string {
  switch (key) {
    case "name":
      return segment.name.toLocaleLowerCase();
    case "distance":
      return segment.distance;
    case "elevation":
      return segment.elev_difference;
    case "grade":
      return segment.avg_grade;
    case "difficulty":
      return segment.difficulty_score;
  }
}

/**
 * Return a new array sorted by the given column/direction. Exported for reuse
 * and to keep the comparison logic testable in isolation.
 */
export function sortSegments(
  segments: SegmentSummary[],
  key: SortKey,
  direction: SortDirection
): SegmentSummary[] {
  const factor = direction === "asc" ? 1 : -1;
  return [...segments].sort((a, b) => {
    const av = sortValue(a, key);
    const bv = sortValue(b, key);
    if (typeof av === "string" && typeof bv === "string") {
      return av.localeCompare(bv) * factor;
    }
    return ((av as number) - (bv as number)) * factor;
  });
}

const COLUMNS: {
  key: SortKey;
  label: string;
  align: "left" | "right";
}[] = [
  { key: "name", label: "Segment Name", align: "left" },
  { key: "distance", label: "Dist (km)", align: "right" },
  { key: "elevation", label: "Elev (m)", align: "right" },
  { key: "grade", label: "Grade", align: "right" },
  { key: "difficulty", label: "Difficulty", align: "left" },
];

function SortableHeader({
  label,
  align,
  active,
  direction,
  onClick,
}: {
  label: string;
  align: "left" | "right";
  active: boolean;
  direction: SortDirection;
  onClick: () => void;
}) {
  const indicator = active
    ? direction === "asc"
      ? "arrow_upward"
      : "arrow_downward"
    : "unfold_more";

  return (
    <th
      aria-sort={active ? (direction === "asc" ? "ascending" : "descending") : "none"}
      className={`px-6 py-3 border-b border-border ${
        align === "right" ? "text-right" : "text-left"
      } ${label === "Segment Name" ? "w-[35%]" : ""}`}
    >
      <button
        type="button"
        onClick={onClick}
        className={`group inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider transition-colors ${
          align === "right" ? "flex-row-reverse" : ""
        } ${active ? "text-primary" : "text-subtle-green hover:text-foreground"}`}
      >
        {label}
        <span
          className={`material-symbols-outlined text-sm leading-none ${
            active ? "opacity-100" : "opacity-40 group-hover:opacity-70"
          }`}
        >
          {indicator}
        </span>
      </button>
    </th>
  );
}

export function SegmentTable({
  segments,
  isLoading,
  onSegmentClick,
}: SegmentTableProps) {
  // null sortKey preserves the incoming order (backend difficulty ranking).
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const displayedSegments = useMemo(() => {
    if (!sortKey) return segments;
    return sortSegments(segments, sortKey, sortDirection);
  }, [segments, sortKey, sortDirection]);

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-bold">Discovered Segments</h3>
          <span className="px-2 py-0.5 rounded-full bg-border text-xs font-bold text-subtle-green">
            {segments.length} Found
          </span>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center justify-center size-8 rounded-full hover:bg-border text-subtle-green transition-colors">
            <span className="material-symbols-outlined text-lg">filter_list</span>
          </button>
          <button className="flex items-center justify-center size-8 rounded-full hover:bg-border text-subtle-green transition-colors">
            <span className="material-symbols-outlined text-lg">download</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-0">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="text-center">
              <span className="material-symbols-outlined text-4xl text-subtle-green animate-spin">
                progress_activity
              </span>
              <p className="text-sm text-subtle-green mt-2">Loading segments...</p>
            </div>
          </div>
        ) : segments.length === 0 ? (
          <div className="flex items-center justify-center h-48">
            <div className="text-center">
              <span className="material-symbols-outlined text-4xl text-subtle-green">
                search
              </span>
              <p className="text-sm text-subtle-green mt-2">
                No segments found. Try a different location.
              </p>
            </div>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead className="bg-background/50 sticky top-0 z-10 backdrop-blur-sm">
              <tr>
                {COLUMNS.map((col) => (
                  <SortableHeader
                    key={col.key}
                    label={col.label}
                    align={col.align}
                    active={sortKey === col.key}
                    direction={sortDirection}
                    onClick={() => handleSort(col.key)}
                  />
                ))}
                <th className="px-6 py-3 text-xs font-semibold text-subtle-green uppercase tracking-wider border-b border-border text-center">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {displayedSegments.map((segment, index) => (
                <SegmentRow
                  key={segment.id}
                  segment={segment}
                  rank={index + 1}
                  onClick={() => onSegmentClick(segment.id)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
