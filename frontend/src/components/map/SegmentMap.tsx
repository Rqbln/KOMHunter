"use client";

/**
 * Map component for displaying segments using Leaflet
 */

import { useEffect, useRef, useState } from "react";
import type { SegmentSummary, SegmentDetails } from "@/types";
import { escapeHtml } from "@/lib/utils";
import { sportIcon, sportLabel, sportColorVar } from "@/lib/sport";

// Dynamically import Leaflet to avoid SSR issues
let L: typeof import("leaflet") | null = null;

interface SegmentMapProps {
  segments: SegmentSummary[];
  selectedSegment: SegmentDetails | null;
  centerLat: number;
  centerLon: number;
  radiusKm: number;
  onSegmentClick: (segmentId: number) => void;
  onCenterChange?: (lat: number, lng: number) => void;
  // Training-heatmap points as [lat, lng] pairs. When non-empty a heat overlay
  // is drawn on top of the map (kept separate from the segment markers); an
  // empty/undefined value removes it.
  heatmapPoints?: [number, number][];
}

export function SegmentMap({
  segments,
  selectedSegment,
  centerLat,
  centerLon,
  radiusKm,
  onSegmentClick,
  onCenterChange,
  heatmapPoints,
}: SegmentMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const circleRef = useRef<L.Circle | null>(null);
  const polylineRef = useRef<L.Polyline | null>(null);
  const heatLayerRef = useRef<L.Layer | null>(null);
  // Hold the latest callback so the map's click handler (registered once in the
  // init effect) always calls the current prop without re-initializing the map.
  const onCenterChangeRef = useRef(onCenterChange);
  const [isMapReady, setIsMapReady] = useState(false);

  useEffect(() => {
    onCenterChangeRef.current = onCenterChange;
  }, [onCenterChange]);

  // Initialize Leaflet
  useEffect(() => {
    const initLeaflet = async () => {
      if (typeof window === "undefined") return;
      
      L = await import("leaflet");
      
      // Fix default marker icon issue with webpack
      delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
        iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
        shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
      });

      if (mapRef.current && !mapInstanceRef.current) {
        // Create map
        const map = L.map(mapRef.current, {
          center: [centerLat, centerLon],
          zoom: 12,
          zoomControl: false,
        });

        // Add tile layer (OpenStreetMap)
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(map);

        // Clicking the map recenters the search around the clicked point.
        map.on("click", (e: L.LeafletMouseEvent) => {
          onCenterChangeRef.current?.(e.latlng.lat, e.latlng.lng);
        });

        mapInstanceRef.current = map;
        setIsMapReady(true);
      }
    };

    initLeaflet();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update map center and radius
  useEffect(() => {
    if (!mapInstanceRef.current || !L || !isMapReady) return;

    const map = mapInstanceRef.current;
    map.setView([centerLat, centerLon], 12);

    // Update or create radius circle
    if (circleRef.current) {
      circleRef.current.setLatLng([centerLat, centerLon]);
      circleRef.current.setRadius(radiusKm * 1000);
    } else {
      circleRef.current = L.circle([centerLat, centerLon], {
        radius: radiusKm * 1000,
        color: "#fc4c02",
        fillColor: "#fc4c02",
        fillOpacity: 0.1,
        weight: 2,
      }).addTo(map);
    }
  }, [centerLat, centerLon, radiusKm, isMapReady]);

  // Update markers when segments change
  useEffect(() => {
    if (!mapInstanceRef.current || !L || !isMapReady) return;

    const map = mapInstanceRef.current;
    const leaflet = L; // Local reference for TypeScript

    // Clear existing markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    // Create custom icon
    const segmentIcon = leaflet.divIcon({
      className: "segment-marker",
      html: `<div class="size-4 bg-primary rounded-full border-2 border-white shadow-lg"></div>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8],
    });

    const selectedIcon = leaflet.divIcon({
      className: "segment-marker-selected",
      html: `<div class="size-6 bg-primary rounded-full border-3 border-white shadow-xl animate-pulse"></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });

    // Add markers for each segment
    segments.forEach((segment) => {
      const isSelected = selectedSegment?.id === segment.id;
      const marker = leaflet.marker(
        [segment.start_latlng[0], segment.start_latlng[1]],
        { icon: isSelected ? selectedIcon : segmentIcon }
      )
        .addTo(map)
        .bindPopup(
          // segment.name is untrusted Strava user-generated content and this
          // is an innerHTML sink (Leaflet bindPopup), so it must be escaped.
          // sportIcon/sportLabel return fixed, controlled strings so they are
          // safe to interpolate without escaping.
          `<div class="font-display">
            <p class="font-bold text-sm">${escapeHtml(segment.name)}</p>
            <p class="text-xs text-gray-600">${(segment.distance / 1000).toFixed(1)}km • ${segment.avg_grade}%</p>
            <p class="text-xs text-gray-500">Score: ${segment.difficulty_score?.toFixed(1) ?? "N/A"}</p>
            <p class="text-xs font-medium" style="display:flex;align-items:center;gap:2px;color:${sportColorVar(segment.activity_type)}">
              <span class="material-symbols-outlined" style="font-size:0.9rem">${sportIcon(segment.activity_type)}</span>
              ${sportLabel(segment.activity_type)}
            </p>
          </div>`
        )
        .on("click", () => onSegmentClick(segment.id));

      markersRef.current.push(marker);
    });

    // Fit bounds to show all markers if we have segments
    if (segments.length > 0) {
      const bounds = leaflet.latLngBounds(
        segments.map((s) => [s.start_latlng[0], s.start_latlng[1]])
      );
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [segments, selectedSegment, onSegmentClick, isMapReady]);

  // Draw polyline for selected segment
  useEffect(() => {
    if (!mapInstanceRef.current || !L || !isMapReady) return;

    const map = mapInstanceRef.current;
    const leaflet = L; // Local reference for TypeScript

    // Remove existing polyline
    if (polylineRef.current) {
      polylineRef.current.remove();
      polylineRef.current = null;
    }

    // Draw polyline if we have a selected segment with a polyline
    if (selectedSegment?.polyline) {
      try {
        // Decode polyline (simple algorithm)
        const decoded = decodePolyline(selectedSegment.polyline);
        if (decoded.length > 0) {
          polylineRef.current = leaflet.polyline(decoded, {
            color: "#fc4c02",
            weight: 4,
            opacity: 0.8,
          }).addTo(map);

          map.fitBounds(polylineRef.current.getBounds(), { padding: [50, 50] });
        }
      } catch (e) {
        console.error("Failed to decode polyline:", e);
      }
    }
  }, [selectedSegment, isMapReady]);

  // Training-heatmap overlay. Kept fully separate from the segment-marker
  // layers: it lazily pulls in the leaflet.heat plugin (which augments the
  // shared module-level Leaflet `L`) only when there are points to show, and
  // rebuilds the layer whenever the points change or removes it when empty.
  useEffect(() => {
    if (!mapInstanceRef.current || !L || !isMapReady) return;

    const map = mapInstanceRef.current;
    const leaflet = L; // Local, non-null reference for TypeScript
    let cancelled = false;

    const removeHeatLayer = () => {
      if (heatLayerRef.current) {
        heatLayerRef.current.remove();
        heatLayerRef.current = null;
      }
    };

    if (!heatmapPoints || heatmapPoints.length === 0) {
      removeHeatLayer();
      return;
    }

    const addHeatLayer = async () => {
      // leaflet.heat has no module exports — it attaches `heatLayer`/`HeatLayer`
      // onto the Leaflet object it require()s. `leaflet` here is the ESM module
      // NAMESPACE, which is sealed/non-extensible, so the plugin cannot add
      // `heatLayer` to it. The real, extensible Leaflet object is the module's
      // default export — augment (and later call) THAT.
      const Lroot = (
        (leaflet as unknown as { default?: typeof leaflet }).default ?? leaflet
      ) as typeof leaflet & {
        heatLayer: (
          points: Array<[number, number, number]>,
          options: Record<string, unknown>
        ) => import("leaflet").Layer;
      };
      (window as unknown as { L: unknown }).L = Lroot;
      await import("leaflet.heat");
      if (cancelled || !mapInstanceRef.current) return;

      // Rebuild from scratch: drop any previous layer before adding the new one.
      removeHeatLayer();

      // leaflet.heat accepts [lat, lng] or [lat, lng, intensity]; give every
      // point a modest intensity so overlapping training routes accumulate into
      // hotter zones.
      const heatData = heatmapPoints.map(
        ([lat, lng]) => [lat, lng, 0.6] as [number, number, number]
      );

      heatLayerRef.current = Lroot
        .heatLayer(heatData, {
          radius: 18,
          blur: 22,
          maxZoom: 17,
          minOpacity: 0.35,
          // Gradient tuned to the Strava orange theme (--primary #fc4c02):
          // faint amber for sparse areas up to a hot orange core.
          gradient: {
            0.2: "rgba(252, 76, 2, 0.15)",
            0.4: "rgba(252, 76, 2, 0.45)",
            0.65: "#fc8a02",
            1.0: "#fc4c02",
          },
        })
        .addTo(map);
    };

    addHeatLayer();

    return () => {
      cancelled = true;
    };
  }, [heatmapPoints, isMapReady]);

  // Zoom controls
  const handleZoomIn = () => {
    mapInstanceRef.current?.zoomIn();
  };

  const handleZoomOut = () => {
    mapInstanceRef.current?.zoomOut();
  };

  return (
    <div className="absolute inset-0">
      {/* Map container */}
      <div ref={mapRef} className="w-full h-full z-0" />

      {/* Loading overlay */}
      {!isMapReady && (
        <div className="absolute inset-0 bg-gray-200 dark:bg-gray-800 flex items-center justify-center">
          <div className="text-center">
            <span className="material-symbols-outlined text-4xl text-subtle-green animate-spin">
              progress_activity
            </span>
            <p className="text-sm text-subtle-green mt-2">Loading map...</p>
          </div>
        </div>
      )}

      {/* Map controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-[1000]">
        <button
          onClick={handleZoomIn}
          className="bg-white dark:bg-surface-dark p-2 rounded-lg shadow-lg hover:bg-gray-50 dark:hover:bg-surface-dark/80 transition-colors"
        >
          <span className="material-symbols-outlined block">add</span>
        </button>
        <button
          onClick={handleZoomOut}
          className="bg-white dark:bg-surface-dark p-2 rounded-lg shadow-lg hover:bg-gray-50 dark:hover:bg-surface-dark/80 transition-colors"
        >
          <span className="material-symbols-outlined block">remove</span>
        </button>
        <button className="bg-white dark:bg-surface-dark p-2 rounded-lg shadow-lg hover:bg-gray-50 dark:hover:bg-surface-dark/80 transition-colors mt-2">
          <span className="material-symbols-outlined block">layers</span>
        </button>
      </div>

      {/* Custom marker styles */}
      <style jsx global>{`
        .segment-marker,
        .segment-marker-selected {
          background: transparent;
          border: none;
        }
        .segment-marker div,
        .segment-marker-selected div {
          background-color: #fc4c02;
        }
        .leaflet-popup-content-wrapper {
          border-radius: 0.75rem;
          font-family: "Lexend", sans-serif;
        }
        .leaflet-popup-tip {
          background: white;
        }
      `}</style>
    </div>
  );
}

/**
 * Decode Google polyline encoding
 */
function decodePolyline(encoded: string): [number, number][] {
  const points: [number, number][] = [];
  let index = 0;
  let lat = 0;
  let lng = 0;

  while (index < encoded.length) {
    let shift = 0;
    let result = 0;
    let byte: number;

    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);

    const dlat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += dlat;

    shift = 0;
    result = 0;

    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);

    const dlng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += dlng;

    points.push([lat / 1e5, lng / 1e5]);
  }

  return points;
}
