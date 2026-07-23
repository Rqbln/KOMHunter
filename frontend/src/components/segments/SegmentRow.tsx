"use client";

/**
 * Individual segment row component
 */

import type { SegmentSummary } from "@/types";
import { formatGrade } from "@/lib/utils";
import { sportIcon, sportLabel, sportColorVar } from "@/lib/sport";

interface SegmentRowProps {
  segment: SegmentSummary;
  rank: number;
  // When true, the table is showing the enriched popularity/competitiveness
  // columns (an enriched sort was used), so this row must render matching cells
  // to keep column alignment. Segments still lacking the metrics render "—".
  showEnrichment?: boolean;
  onClick: () => void;
}

function getDifficultyLabel(score: number): { label: string; color: string } {
  if (score < 25) return { label: "Easy", color: "bg-green-100 text-green-700" };
  if (score < 50) return { label: "Moderate", color: "bg-yellow-100 text-yellow-700" };
  if (score < 75) return { label: "Hard", color: "bg-orange-100 text-orange-700" };
  return { label: "Expert", color: "bg-red-100 text-red-700" };
}

/** Compact enrichment metric cell: an orange badge, or an em dash when absent. */
function MetricCell({
  value,
  title,
}: {
  value: number | null | undefined;
  title?: string;
}) {
  return (
    <td className="px-6 py-4 whitespace-nowrap text-right">
      {value == null ? (
        <span className="text-sm text-subtle-green">—</span>
      ) : (
        <span
          title={title}
          className="inline-block px-2 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary"
        >
          {Math.round(value)}
        </span>
      )}
    </td>
  );
}

export function SegmentRow({
  segment,
  rank,
  showEnrichment,
  onClick,
}: SegmentRowProps) {
  const difficulty = getDifficultyLabel(segment.difficulty_score);
  const isTopRanked = rank <= 3;

  // Tooltip context for the enrichment badges (only when data is present).
  const popularityTitle =
    segment.effort_count != null || segment.athlete_count != null
      ? `Le plus fréquenté d'abord · ${segment.effort_count ?? "?"} passages, ${
          segment.athlete_count ?? "?"
        } athlètes`
      : "Le plus fréquenté d'abord";
  const competitivenessTitle = segment.kom_time
    ? `KOM le plus lent d'abord (plus facile à gagner) · KOM ${segment.kom_time}`
    : "KOM le plus lent d'abord (plus facile à gagner)";

  return (
    <tr
      className="group hover:bg-primary/5 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center gap-3">
          <div
            className={`flex-shrink-0 size-8 rounded-full flex items-center justify-center ${
              isTopRanked
                ? "bg-primary/20 text-primary"
                : "bg-border text-subtle-green"
            }`}
          >
            {isTopRanked ? (
              <span className="material-symbols-outlined text-sm font-bold">
                star
              </span>
            ) : (
              <span className="material-symbols-outlined text-sm">landscape</span>
            )}
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <p className="text-sm font-bold group-hover:text-primary transition-colors">
                {segment.name}
              </p>
              <span
                className="material-symbols-outlined text-sm leading-none"
                style={{ color: sportColorVar(segment.activity_type) }}
                title={sportLabel(segment.activity_type)}
                aria-label={sportLabel(segment.activity_type)}
              >
                {sportIcon(segment.activity_type)}
              </span>
              {segment.kom_suspicious && (
                <span
                  className="material-symbols-outlined text-sm leading-none text-red-500"
                  title="Temps KOM douteux (probable erreur GPS)"
                  aria-label="Temps KOM douteux"
                >
                  warning
                </span>
              )}
            </div>
            <p className="text-xs text-subtle-green">
              Cat {segment.climb_category || "NC"}
            </p>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
        {(segment.distance / 1000).toFixed(1)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
        {Math.round(segment.elev_difference)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
        {formatGrade(segment.avg_grade)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span
          className={`px-2 py-1 rounded-full text-xs font-bold ${difficulty.color}`}
        >
          {difficulty.label}
        </span>
      </td>
      {showEnrichment && (
        <>
          <MetricCell value={segment.prestige_score} title={popularityTitle} />
          <MetricCell
            value={segment.competitiveness_score}
            title={competitivenessTitle}
          />
        </>
      )}
      <td className="px-6 py-4 whitespace-nowrap text-center">
        <button className="text-subtle-green hover:text-primary transition-colors">
          <span className="material-symbols-outlined text-lg">visibility</span>
        </button>
      </td>
    </tr>
  );
}
