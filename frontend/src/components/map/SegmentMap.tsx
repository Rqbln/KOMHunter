"use client";

/**
 * Map component for displaying segments using Leaflet
 */

import { useEffect, useRef, useState } from "react";
import type { SegmentSummary, SegmentDetails } from "@/types";

// Dynamically import Leaflet to avoid SSR issues
let L: typeof import("leaflet") | null = null;

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
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const circleRef = useRef<L.Circle | null>(null);
  const polylineRef = useRef<L.Polyline | null>(null);
  const [isMapReady, setIsMapReady] = useState(false);

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
        color: "#0df259",
        fillColor: "#0df259",
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
          `<div class="font-display">
            <p class="font-bold text-sm">${segment.name}</p>
            <p class="text-xs text-gray-600">${(segment.distance / 1000).toFixed(1)}km • ${segment.avg_grade}%</p>
            <p class="text-xs text-gray-500">Score: ${segment.difficulty_score?.toFixed(1) ?? "N/A"}</p>
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
            color: "#0df259",
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
          background-color: #0df259;
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
