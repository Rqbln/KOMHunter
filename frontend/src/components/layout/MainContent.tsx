"use client";

/**
 * Main content area with map and segment table
 */

import { SegmentMap } from "@/components/map/SegmentMap";
import { SegmentTable } from "@/components/segments/SegmentTable";
import type { SegmentSummary, SegmentDetails } from "@/types";

interface MainContentProps {
  className?: string;
  segments: SegmentSummary[];
  selectedSegment: SegmentDetails | null;
  centerLat: number;
  centerLon: number;
  radiusKm: number;
  isLoading?: boolean;
  onSegmentSelect: (segmentId: number) => void;
}

export function MainContent({
  className,
  segments,
  selectedSegment,
  centerLat,
  centerLon,
  radiusKm,
  isLoading,
  onSegmentSelect,
}: MainContentProps) {
  return (
    <main
      className={`flex-1 flex flex-col min-w-0 bg-background relative overflow-hidden ${className}`}
    >
      {/* Map Section */}
      <div className="h-[55%] w-full relative group">
        <SegmentMap
          segments={segments}
          selectedSegment={selectedSegment}
          centerLat={centerLat}
          centerLon={centerLon}
          radiusKm={radiusKm}
          onSegmentClick={onSegmentSelect}
        />
      </div>

      {/* Data Table Section */}
      <div className="flex-1 overflow-hidden flex flex-col bg-surface border-t border-border shadow-[0_-4px_20px_rgba(0,0,0,0.05)] z-10 rounded-t-2xl -mt-4 relative">
        <SegmentTable
          segments={segments}
          isLoading={isLoading}
          onSegmentClick={onSegmentSelect}
        />
      </div>
    </main>
  );
}
