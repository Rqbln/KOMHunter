"use client";

/**
 * Main content area with map, segment table, and detail panel
 */

import { useState } from "react";
import { SegmentMap } from "@/components/map/SegmentMap";
import { SegmentTable } from "@/components/segments/SegmentTable";
import { SegmentDetailPanel } from "@/components/segments/SegmentDetailPanel";
import type { SegmentSummary, SegmentDetails, HeatmapSport } from "@/types";
import { HEATMAP_SPORTS } from "@/lib/heatmapSport";

interface MainContentProps {
  className?: string;
  segments: SegmentSummary[];
  selectedSegment: SegmentDetails | null;
  centerLat: number;
  centerLon: number;
  radiusKm: number;
  // Bumped on a logo reset to snap the map back to the default location/zoom.
  viewResetKey?: number;
  isLoading?: boolean;
  isLoadingDetails?: boolean;
  onSegmentSelect: (segmentId: number) => void;
  onClearSelection?: () => void;
  onCenterChange?: (lat: number, lng: number) => void;
  // Training-heatmap overlay + control. The control is only shown when
  // `heatmapAvailable` (i.e. the user is logged in). `heatmapPoints` are the
  // points to render (already gated on the enabled state by the parent).
  heatmapPoints?: [number, number][];
  heatmapAvailable?: boolean;
  heatmapEnabled?: boolean;
  heatmapSport?: HeatmapSport;
  isHeatmapLoading?: boolean;
  onHeatmapToggle?: () => void;
  onHeatmapSportChange?: (sport: HeatmapSport) => void;
}

export function MainContent({
  className,
  segments,
  selectedSegment,
  centerLat,
  centerLon,
  radiusKm,
  viewResetKey,
  isLoading,
  isLoadingDetails,
  onSegmentSelect,
  onClearSelection,
  onCenterChange,
  heatmapPoints,
  heatmapAvailable,
  heatmapEnabled,
  heatmapSport = "all",
  isHeatmapLoading,
  onHeatmapToggle,
  onHeatmapSportChange,
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
      {/* Map Section. `isolate z-0` makes this its own stacking context sitting
          below the app drawers (fixed z-50), so neither these overlays nor
          Leaflet's internal controls can ever paint over an open drawer. */}
      <div className="h-[55%] w-full relative group isolate z-0">
        <SegmentMap
          segments={segments}
          selectedSegment={selectedSegment}
          centerLat={centerLat}
          centerLon={centerLon}
          radiusKm={radiusKm}
          viewResetKey={viewResetKey}
          onSegmentClick={onSegmentSelect}
          onCenterChange={onCenterChange}
          heatmapPoints={heatmapPoints}
        />

        {/* Training-heatmap control (only meaningful when logged in) */}
        {heatmapAvailable && (
          <div className="absolute top-4 left-4 z-30 flex flex-col items-start gap-2">
            <button
              type="button"
              onClick={onHeatmapToggle}
              aria-pressed={heatmapEnabled}
              title="Heatmap d'entraînement"
              className={`flex items-center gap-2 px-3 py-2 rounded-lg shadow-lg transition-colors text-sm font-medium ${
                heatmapEnabled
                  ? "bg-primary text-white hover:bg-primary/90"
                  : "bg-white dark:bg-surface-dark hover:bg-gray-50 dark:hover:bg-surface-dark/80"
              }`}
            >
              <span
                className={`material-symbols-outlined text-base leading-none ${
                  isHeatmapLoading ? "animate-spin" : ""
                }`}
              >
                {isHeatmapLoading ? "progress_activity" : "whatshot"}
              </span>
              <span className="hidden sm:inline">Heatmap d&apos;entraînement</span>
            </button>

            {heatmapEnabled && (
              <div className="flex items-center gap-1 bg-white dark:bg-surface-dark p-1 rounded-lg shadow-lg">
                {HEATMAP_SPORTS.map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => onHeatmapSportChange?.(value)}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                      heatmapSport === value
                        ? "bg-primary text-white"
                        : "text-subtle-green hover:bg-gray-100 dark:hover:bg-surface-dark/60"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Zone-selection hint */}
        <div className="absolute bottom-4 left-4 z-20 pointer-events-none bg-surface/90 backdrop-blur px-3 py-1.5 rounded-full shadow-lg flex items-center gap-1.5 text-xs text-subtle-green">
          <span className="material-symbols-outlined text-sm leading-none">ads_click</span>
          Cliquez sur la carte pour recentrer la recherche
        </div>

        {/* Loading indicator for segment details. Top-center so it never shares
            the top-right corner with the map's layer switch. */}
        {isLoadingDetails && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-surface px-3 py-2 rounded-lg shadow-lg flex items-center gap-2 z-30">
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
