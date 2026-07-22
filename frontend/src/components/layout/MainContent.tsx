"use client";

/**
 * Main content area with map, segment table, and detail panel
 */

import { useState } from "react";
import { SegmentMap } from "@/components/map/SegmentMap";
import { SegmentTable } from "@/components/segments/SegmentTable";
import { SegmentDetailPanel } from "@/components/segments/SegmentDetailPanel";
import type { SegmentSummary, SegmentDetails } from "@/types";

interface MainContentProps {
  className?: string;
  segments: SegmentSummary[];
  selectedSegment: SegmentDetails | null;
  centerLat: number;
  centerLon: number;
  radiusKm: number;
  isLoading?: boolean;
  isLoadingDetails?: boolean;
  onSegmentSelect: (segmentId: number) => void;
  onClearSelection?: () => void;
}

export function MainContent({
  className,
  segments,
  selectedSegment,
  centerLat,
  centerLon,
  radiusKm,
  isLoading,
  isLoadingDetails,
  onSegmentSelect,
  onClearSelection,
}: MainContentProps) {
  // The panel is open purely as a function of the current selection — no
  // render-phase setState and no setState-in-effect. On close we flag the
  // segment being dismissed so the slide-out animation can play before the
  // parent clears the selection (300ms later).
  const [closingSegmentId, setClosingSegmentId] = useState<number | null>(null);
  const isPanelOpen = !!selectedSegment && selectedSegment.id !== closingSegmentId;

  const handleClosePanel = () => {
    const closingId = selectedSegment?.id ?? null;
    setClosingSegmentId(closingId);
    // Clear selection after the close animation, then reset the closing flag.
    setTimeout(() => {
      onClearSelection?.();
      setClosingSegmentId(null);
    }, 300);
  };

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
        
        {/* Loading indicator for segment details */}
        {isLoadingDetails && (
          <div className="absolute top-4 right-4 bg-surface px-3 py-2 rounded-lg shadow-lg flex items-center gap-2 z-20">
            <div className="size-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-sm">Chargement...</span>
          </div>
        )}
      </div>

      {/* Data Table Section */}
      <div className="flex-1 overflow-hidden flex flex-col bg-surface border-t border-border shadow-[0_-4px_20px_rgba(0,0,0,0.05)] z-10 rounded-t-2xl -mt-4 relative">
        <SegmentTable
          segments={segments}
          isLoading={isLoading}
          onSegmentClick={onSegmentSelect}
        />
      </div>
      
      {/* Segment Detail Panel */}
      <SegmentDetailPanel
        segment={selectedSegment}
        isOpen={isPanelOpen}
        onClose={handleClosePanel}
      />
    </main>
  );
}
