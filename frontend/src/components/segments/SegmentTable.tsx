"use client";

/**
 * Segment table component for displaying discovered segments.
 *
 * Column headers (Name, Distance, Elevation, Grade, Difficulty) are sortable:
 * clicking a header sorts by that column and toggles asc/desc, with an arrow
 * indicator. Sorting is controlled locally so both the home and search pages
 * benefit without extra wiring.
 *
 * When the results carry enrichment metrics (fetched via an enriched server
 * sort — popularity | competitiveness | opportunity) two extra sortable columns
 * appear, "Popularité" (prestige_score) and "Compétitivité"
 * (competitiveness_score). They stay hidden otherwise so non-enriched results
 * don't show empty columns. Segments missing the metric sort last.
 */

import { useMemo, useState } from "react";
import { SegmentRow } from "./SegmentRow";
import type { SegmentSummary } from "@/types";

interface SegmentTableProps {
  segments: SegmentSummary[];
  isLoading?: boolean;
  onSegmentClick: (segmentId: number) => void;
}

type SortKey =
  | "name"
  | "distance"
  | "elevation"
  | "grade"
  | "difficulty"
  | "popularity"
  | "competitiveness";
type SortDirection = "asc" | "desc";

/**
 * Extract the comparable value for a given sort column. The enrichment columns
 * (popularity / competitiveness) may be null when the result set was not
 * fetched with an enriched sort; null is handled explicitly by the comparator.
 */
function sortValue(
  segment: SegmentSummary,
  key: SortKey
): number | string | null {
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
    case "popularity":
      return segment.prestige_score ?? null;
    case "competitiveness":
      return segment.competitiveness_score ?? null;
  }
}

/**
 * Return a new array sorted by the given column/direction. Exported for reuse
 * and to keep the comparison logic testable in isolation. Segments missing the
 * comparable value (null — i.e. not enriched) always sort LAST, regardless of
 * direction, matching the server-side "enrichment missing sorts last" contract.
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
    if (av === null && bv === null) return 0;
    if (av === null) return 1;
    if (bv === null) return -1;
    if (typeof av === "string" && typeof bv === "string") {
      return av.localeCompare(bv) * factor;
    }
    return ((av as number) - (bv as number)) * factor;
  });
}

type Column = { key: SortKey; label: string; align: "left" | "right" };

/** Always-present terrain columns. */
const BASE_COLUMNS: Column[] = [
  { key: "name", label: "Segment Name", align: "left" },
  { key: "distance", label: "Dist (km)", align: "right" },
  { key: "elevation", label: "Elev (m)", align: "right" },
  { key: "grade", label: "Grade", align: "right" },
  { key: "difficulty", label: "Difficulty", align: "left" },
];

/** Extra columns shown only when the results carry enrichment metrics. */
const ENRICHMENT_COLUMNS: Column[] = [
  { key: "popularity", label: "Popularité", align: "right" },
  { key: "competitiveness", label: "Compétitivité", align: "right" },
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

  // Show the popularity/competitiveness columns only when the current results
  // were fetched with an enriched sort (any segment carries the metrics).
  // Otherwise these fields are absent and empty columns would be noise.
  const hasEnrichment = useMemo(
    () =>
      segments.some(
        (s) => s.prestige_score != null || s.competitiveness_score != null
      ),
    [segments]
  );

  const columns = useMemo(
    () => (hasEnrichment ? [...BASE_COLUMNS, ...ENRICHMENT_COLUMNS] : BASE_COLUMNS),
    [hasEnrichment]
  );

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
                {columns.map((col) => (
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
                  showEnrichment={hasEnrichment}
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
