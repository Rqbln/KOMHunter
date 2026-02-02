"use client";

/**
 * Map component for displaying segments
 * 
 * TODO: Integrate with Leaflet or Mapbox GL for actual map rendering
 * This is a placeholder stub for the technical phase
 */

import type { SegmentSummary, SegmentDetails } from "@/types";

interface SegmentMapProps {
  segments: SegmentSummary[];
  selectedSegment: SegmentDetails | null;
  centerLat: number;
  centerLon: number;
  radiusKm: number;
  onSegmentClick: (segmentId: number) => void;
}

export function SegmentMap({
  segments,
  selectedSegment,
  centerLat,
  centerLon,
  radiusKm,
  onSegmentClick,
}: SegmentMapProps) {
  return (
    <div className="absolute inset-0 bg-gray-200 dark:bg-gray-800">
      {/* Placeholder map background */}
      <div className="absolute inset-0 flex items-center justify-center text-subtle-green">
        <div className="text-center">
          <span className="material-symbols-outlined text-6xl mb-2">map</span>
          <p className="text-sm font-medium">Map Component</p>
          <p className="text-xs mt-1">
            Center: {centerLat.toFixed(4)}, {centerLon.toFixed(4)}
          </p>
          <p className="text-xs">Radius: {radiusKm} km</p>
          <p className="text-xs mt-2">{segments.length} segments to display</p>
        </div>
      </div>

      {/* Search radius indicator */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 size-48 rounded-full border-2 border-primary/30 bg-primary/10 animate-pulse pointer-events-none" />

      {/* Map controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
        <button className="bg-white dark:bg-surface-dark p-2 rounded-lg shadow-lg hover:bg-gray-50 dark:hover:bg-surface-dark/80 transition-colors">
          <span className="material-symbols-outlined block">add</span>
        </button>
        <button className="bg-white dark:bg-surface-dark p-2 rounded-lg shadow-lg hover:bg-gray-50 dark:hover:bg-surface-dark/80 transition-colors">
          <span className="material-symbols-outlined block">remove</span>
        </button>
        <button className="bg-white dark:bg-surface-dark p-2 rounded-lg shadow-lg hover:bg-gray-50 dark:hover:bg-surface-dark/80 transition-colors mt-2">
          <span className="material-symbols-outlined block">layers</span>
        </button>
      </div>

      {/* Sample markers for demonstration */}
      {segments.slice(0, 3).map((segment, index) => (
        <div
          key={segment.id}
          className="absolute group/marker cursor-pointer"
          style={{
            top: `${30 + index * 15}%`,
            left: `${40 + index * 10}%`,
          }}
          onClick={() => onSegmentClick(segment.id)}
        >
          <div className="size-4 bg-primary rounded-full border-2 border-white shadow-lg transform transition-transform group-hover/marker:scale-125" />
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white dark:bg-surface-dark px-3 py-1.5 rounded-lg shadow-xl opacity-0 group-hover/marker:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
            <p className="text-xs font-bold">{segment.name}</p>
            <p className="text-[10px] text-subtle-green">
              {(segment.distance / 1000).toFixed(1)}km • {segment.avg_grade}%
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
