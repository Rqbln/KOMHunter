"use client";

/**
 * Segment table component for displaying discovered segments
 */

import { SegmentRow } from "./SegmentRow";
import type { SegmentSummary } from "@/types";

interface SegmentTableProps {
  segments: SegmentSummary[];
  isLoading?: boolean;
  onSegmentClick: (segmentId: number) => void;
}

export function SegmentTable({
  segments,
  isLoading,
  onSegmentClick,
}: SegmentTableProps) {
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
                <th className="px-6 py-3 text-xs font-semibold text-subtle-green uppercase tracking-wider border-b border-border w-[35%]">
                  Segment Name
                </th>
                <th className="px-6 py-3 text-xs font-semibold text-subtle-green uppercase tracking-wider border-b border-border text-right">
                  Dist (km)
                </th>
                <th className="px-6 py-3 text-xs font-semibold text-subtle-green uppercase tracking-wider border-b border-border text-right">
                  Elev (m)
                </th>
                <th className="px-6 py-3 text-xs font-semibold text-subtle-green uppercase tracking-wider border-b border-border text-right">
                  Grade
                </th>
                <th className="px-6 py-3 text-xs font-semibold text-subtle-green uppercase tracking-wider border-b border-border">
                  Difficulty
                </th>
                <th className="px-6 py-3 text-xs font-semibold text-subtle-green uppercase tracking-wider border-b border-border text-center">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {segments.map((segment, index) => (
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
