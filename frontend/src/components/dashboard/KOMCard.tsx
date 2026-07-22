"use client";

/**
 * Individual KOM card component
 */

import type { AthleteKOM, SegmentEffort, StarredSegment } from "@/types";
import { sportIcon, sportLabel, sportColorVar } from "@/lib/sport";

interface KOMCardProps {
  kom: AthleteKOM;
  onClick?: () => void;
}

interface PRCardProps {
  pr: SegmentEffort;
  onClick?: () => void;
}

interface StarredSegmentCardProps {
  segment: StarredSegment;
  onClick?: () => void;
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatDistance(meters: number): string {
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)} km`;
  }
  return `${meters.toFixed(0)} m`;
}

export function KOMCard({ kom, onClick }: KOMCardProps) {
  return (
    <div 
      className="bg-surface border border-border rounded-xl p-4 hover:border-primary/50 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="material-symbols-outlined text-yellow-500 text-lg">emoji_events</span>
            <h4 className="font-bold text-sm truncate">{kom.segment_name}</h4>
          </div>
          <div className="flex items-center gap-4 text-xs text-subtle-green">
            <span>{formatDistance(kom.distance)}</span>
            <span>{kom.avg_grade.toFixed(1)}%</span>
            <span>{formatDate(kom.start_date_local)}</span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xl font-bold text-primary">{kom.elapsed_time_formatted}</p>
          {kom.kom_rank === 1 && (
            <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full font-medium">
              KOM
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export function PRCard({ pr, onClick }: PRCardProps) {
  const getPRBadge = (rank: number | undefined) => {
    if (!rank) return null;
    if (rank === 1) return { label: "PR", color: "bg-green-100 text-green-700" };
    if (rank === 2) return { label: "2e PR", color: "bg-blue-100 text-blue-700" };
    if (rank === 3) return { label: "3e PR", color: "bg-purple-100 text-purple-700" };
    return null;
  };

  const badge = getPRBadge(pr.pr_rank);

  return (
    <div 
      className="bg-surface border border-border rounded-xl p-4 hover:border-primary/50 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="material-symbols-outlined text-green-500 text-lg">timer</span>
            <h4 className="font-bold text-sm truncate">{pr.segment_name}</h4>
          </div>
          <div className="flex items-center gap-4 text-xs text-subtle-green">
            <span>{formatDistance(pr.distance)}</span>
            <span>{formatDate(pr.start_date_local)}</span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xl font-bold">{pr.elapsed_time_formatted}</p>
          <div className="flex gap-1 justify-end mt-1">
            {badge && (
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.color}`}>
                {badge.label}
              </span>
            )}
            {pr.kom_rank && pr.kom_rank <= 10 && (
              <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-medium">
                Top {pr.kom_rank}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function StarredSegmentCard({ segment, onClick }: StarredSegmentCardProps) {
  const getCategoryLabel = (cat: number) => {
    switch (cat) {
      case 5: return "HC";
      case 1: return "Cat 1";
      case 2: return "Cat 2";
      case 3: return "Cat 3";
      case 4: return "Cat 4";
      default: return "NC";
    }
  };

  return (
    <div 
      className="bg-surface border border-border rounded-xl p-4 hover:border-primary/50 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="material-symbols-outlined text-yellow-400 text-lg">star</span>
            <h4 className="font-bold text-sm truncate">{segment.name}</h4>
          </div>
          <div className="flex items-center gap-4 text-xs text-subtle-green">
            <span>{formatDistance(segment.distance)}</span>
            <span>{segment.avg_grade.toFixed(1)}%</span>
            <span>{segment.city || segment.country}</span>
          </div>
        </div>
        <div className="text-right">
          <span className="text-xs bg-border px-2 py-1 rounded-full font-medium">
            {getCategoryLabel(segment.climb_category)}
          </span>
          <p
            className="text-xs mt-1 flex items-center justify-end gap-1 font-medium"
            style={{ color: sportColorVar(segment.activity_type) }}
          >
            <span className="material-symbols-outlined text-sm leading-none">
              {sportIcon(segment.activity_type)}
            </span>
            {sportLabel(segment.activity_type)}
          </p>
        </div>
      </div>
    </div>
  );
}
