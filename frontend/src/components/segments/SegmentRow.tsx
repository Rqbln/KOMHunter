"use client";

/**
 * Individual segment row component
 */

import type { SegmentSummary } from "@/types";
import { formatDistance, formatGrade, formatElevation } from "@/lib/utils";

interface SegmentRowProps {
  segment: SegmentSummary;
  rank: number;
  onClick: () => void;
}

function getDifficultyLabel(score: number): { label: string; color: string } {
  if (score < 25) return { label: "Easy", color: "bg-green-100 text-green-700" };
  if (score < 50) return { label: "Moderate", color: "bg-yellow-100 text-yellow-700" };
  if (score < 75) return { label: "Hard", color: "bg-orange-100 text-orange-700" };
  return { label: "Expert", color: "bg-red-100 text-red-700" };
}

export function SegmentRow({ segment, rank, onClick }: SegmentRowProps) {
  const difficulty = getDifficultyLabel(segment.difficulty_score);
  const isTopRanked = rank <= 3;

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
            <p className="text-sm font-bold group-hover:text-primary transition-colors">
              {segment.name}
            </p>
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
      <td className="px-6 py-4 whitespace-nowrap text-center">
        <button className="text-subtle-green hover:text-primary transition-colors">
          <span className="material-symbols-outlined text-lg">visibility</span>
        </button>
      </td>
    </tr>
  );
}
