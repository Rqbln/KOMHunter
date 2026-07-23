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
 *
 * The header exposes two client-side tools over the already-loaded rows (no
 * re-fetch):
 *   - a FILTER popover (hide suspicious-KOM rows, minimum-difficulty slider);
 *   - a DOWNLOAD button that exports the currently displayed rows to CSV.
 * Both operate on the in-memory result set and compose with the column sort.
 */

import { useEffect, useMemo, useRef, useState } from "react";
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

/** Human-readable difficulty bucket derived from difficulty_score (0–100). */
export function difficultyLabel(score: number): string {
  if (score < 25) return "Easy";
  if (score < 50) return "Moderate";
  if (score < 75) return "Hard";
  return "Expert";
}

export interface SegmentDisplayFilters {
  /** Hide rows whose KOM time is flagged as suspicious (likely GPS error). */
  hideSuspicious: boolean;
  /** Only keep rows with difficulty_score >= this threshold (0 = no floor). */
  minDifficulty: number;
}

export const DEFAULT_DISPLAY_FILTERS: SegmentDisplayFilters = {
  hideSuspicious: false,
  minDifficulty: 0,
};

/**
 * Apply client-side display filters to the already-loaded rows. Pure and
 * exported for testing. Does not re-fetch or mutate the input.
 */
export function filterSegments(
  segments: SegmentSummary[],
  filters: SegmentDisplayFilters
): SegmentSummary[] {
  return segments.filter((s) => {
    if (filters.hideSuspicious && s.kom_suspicious) return false;
    if (s.difficulty_score < filters.minDifficulty) return false;
    return true;
  });
}

/** Quote a CSV cell when it contains a delimiter, quote, or newline (RFC 4180). */
function csvCell(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

const CSV_HEADER = [
  "name",
  "distance_km",
  "avg_grade",
  "difficulty_score",
  "category",
  "prestige_score",
  "competitiveness_score",
  "kom_time",
  "strava_url",
];

/**
 * Serialize the given segments to a CSV string (RFC 4180, CRLF line endings).
 * Pure and exported for testing; the download side effect lives in the handler.
 */
export function segmentsToCsv(segments: SegmentSummary[]): string {
  const rows = segments.map((s) => [
    s.name,
    (s.distance / 1000).toFixed(2),
    s.avg_grade.toFixed(1),
    Math.round(s.difficulty_score),
    difficultyLabel(s.difficulty_score),
    s.prestige_score == null ? "" : Math.round(s.prestige_score),
    s.competitiveness_score == null ? "" : Math.round(s.competitiveness_score),
    s.kom_time ?? "",
    `https://www.strava.com/segments/${s.id}`,
  ]);
  return [CSV_HEADER, ...rows]
    .map((row) => row.map(csvCell).join(","))
    .join("\r\n");
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

  // Client-side display filters over the already-loaded rows (no re-fetch).
  const [filters, setFilters] = useState<SegmentDisplayFilters>(
    DEFAULT_DISPLAY_FILTERS
  );
  const [filterOpen, setFilterOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);

  const filtersActive =
    filters.hideSuspicious || filters.minDifficulty > 0;

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  // Close the filter popover on outside pointer-down and on Escape.
  useEffect(() => {
    if (!filterOpen) return;
    function handlePointerDown(event: MouseEvent) {
      if (
        filterRef.current &&
        !filterRef.current.contains(event.target as Node)
      ) {
        setFilterOpen(false);
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setFilterOpen(false);
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [filterOpen]);

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

  // Filter first (over the loaded rows), then apply the active column sort.
  const filteredSegments = useMemo(
    () => filterSegments(segments, filters),
    [segments, filters]
  );

  const displayedSegments = useMemo(() => {
    if (!sortKey) return filteredSegments;
    return sortSegments(filteredSegments, sortKey, sortDirection);
  }, [filteredSegments, sortKey, sortDirection]);

  const handleDownload = () => {
    if (displayedSegments.length === 0) return;
    // Prepend a UTF-8 BOM so Excel renders accented segment names correctly.
    const csv = "\uFEFF" + segmentsToCsv(displayedSegments);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `komhunter-segments-${new Date()
      .toISOString()
      .slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const noSegments = segments.length === 0;
  const noMatches = !noSegments && displayedSegments.length === 0;

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-bold">Discovered Segments</h3>
          <span className="px-2 py-0.5 rounded-full bg-border text-xs font-bold text-subtle-green">
            {filtersActive
              ? `${displayedSegments.length} / ${segments.length}`
              : `${segments.length} Found`}
          </span>
        </div>
        <div className="flex gap-2">
          {/* Filter popover */}
          <div ref={filterRef} className="relative">
            <button
              type="button"
              onClick={() => setFilterOpen((prev) => !prev)}
              aria-label="Filtrer les segments"
              aria-haspopup="dialog"
              aria-expanded={filterOpen}
              title="Filtres d'affichage"
              className={`flex items-center justify-center size-8 rounded-full transition-colors relative ${
                filtersActive
                  ? "bg-primary/15 text-primary"
                  : "hover:bg-border text-subtle-green"
              }`}
            >
              <span className="material-symbols-outlined text-lg">
                filter_list
              </span>
              {filtersActive && (
                <span
                  aria-hidden="true"
                  className="absolute top-1 right-1 size-1.5 bg-primary rounded-full"
                />
              )}
            </button>

            {filterOpen && (
              <div
                role="dialog"
                aria-label="Filtres d'affichage"
                className="absolute right-0 top-full mt-2 w-72 rounded-xl border border-border bg-surface shadow-lg z-30 p-4"
              >
                <div className="flex items-center justify-between gap-2 mb-3">
                  <h4 className="text-sm font-bold">Filtres d&apos;affichage</h4>
                  {filtersActive && (
                    <button
                      type="button"
                      onClick={() => setFilters(DEFAULT_DISPLAY_FILTERS)}
                      className="text-xs font-medium text-primary hover:underline"
                    >
                      Réinitialiser
                    </button>
                  )}
                </div>

                <label className="flex items-center gap-2 cursor-pointer py-1">
                  <input
                    type="checkbox"
                    checked={filters.hideSuspicious}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        hideSuspicious: e.target.checked,
                      }))
                    }
                    className="size-4 accent-primary"
                  />
                  <span className="text-sm">
                    Masquer les segments au KOM douteux
                  </span>
                </label>

                <div className="mt-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">Difficulté minimale</span>
                    <span className="text-xs font-bold text-primary">
                      {filters.minDifficulty}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    step={5}
                    value={filters.minDifficulty}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        minDifficulty: Number(e.target.value),
                      }))
                    }
                    className="w-full accent-primary"
                    aria-label="Difficulté minimale"
                  />
                </div>

                <p className="mt-3 text-xs text-subtle-green">
                  Filtres locaux — appliqués aux résultats déjà chargés, sans
                  nouvelle recherche.
                </p>
              </div>
            )}
          </div>

          {/* CSV download */}
          <button
            type="button"
            onClick={handleDownload}
            disabled={displayedSegments.length === 0}
            aria-label="Exporter en CSV"
            title="Exporter les segments affichés (CSV)"
            className="flex items-center justify-center size-8 rounded-full hover:bg-border text-subtle-green transition-colors disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
          >
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
        ) : noSegments ? (
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
        ) : noMatches ? (
          <div className="flex items-center justify-center h-48">
            <div className="text-center">
              <span className="material-symbols-outlined text-4xl text-subtle-green">
                filter_list_off
              </span>
              <p className="text-sm text-subtle-green mt-2">
                Aucun segment ne correspond aux filtres.
              </p>
              <button
                type="button"
                onClick={() => setFilters(DEFAULT_DISPLAY_FILTERS)}
                className="text-sm text-primary hover:underline mt-1"
              >
                Réinitialiser les filtres
              </button>
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
