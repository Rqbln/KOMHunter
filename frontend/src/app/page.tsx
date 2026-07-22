"use client";

/**
 * KOMHunter Main Page
 */

import { useState, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { MainContent } from "@/components/layout/MainContent";
import { UserDashboard } from "@/components/dashboard/UserDashboard";
import { useSegments, useStrava } from "@/hooks";
import type { HuntParameters } from "@/types";

/** Human-readable label for a map-picked point (no reverse geocoding). */
function formatCoordLabel(lat: number, lon: number): string {
  return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
}

function HomePageContent() {
  const [huntParams, setHuntParams] = useState<HuntParameters | null>(null);
  // `center` is the single source of truth for the search area: it drives the
  // map view/radius circle AND feeds the sidebar form's coordinates, so a map
  // click and a "Start Hunt" agree on where to search. `location` is the label
  // shown in the form's text field for that same point.
  const [center, setCenter] = useState({ lat: 48.8566, lon: 2.3522 });
  const [location, setLocation] = useState("Paris, France");
  const [isDashboardOpen, setIsDashboardOpen] = useState(false);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);

  const { isAuthenticated, login } = useStrava();

  const {
    segments,
    selectedSegment,
    isLoading,
    isLoadingDetails,
    error,
    totalCount,
    explore,
    selectSegment,
    clearSelection,
  } = useSegments();

  const handleStartHunt = useCallback(
    async (params: HuntParameters) => {
      if (!isAuthenticated) {
        // No API call without a session: prompt the user to log in instead
        setShowLoginPrompt(true);
        return;
      }
      setShowLoginPrompt(false);
      // params.latitude/longitude already come from `center` (the form reads it
      // as a controlled prop), so no need to re-sync the map here.
      setHuntParams(params);
      await explore(params);
    },
    [explore, isAuthenticated]
  );

  // Geocoding / "my location" from the sidebar form updates the shared center.
  const handleLocationChange = useCallback(
    (newLocation: string, lat: number, lon: number) => {
      setLocation(newLocation);
      setCenter({ lat, lon });
    },
    []
  );

  const handleSegmentSelect = useCallback(
    async (segmentId: number) => {
      await selectSegment(segmentId);
    },
    [selectSegment]
  );

  // Clicking the map recenters the search: update the shared `center` (which the
  // sidebar form reads as its coordinates) and relabel the form's location field
  // to the picked point, so the next "Start Hunt" searches here. Deliberately
  // does not auto re-run explore — recentering stays predictable.
  const handleCenterChange = useCallback((lat: number, lng: number) => {
    setCenter({ lat, lon: lng });
    setLocation(formatCoordLabel(lat, lng));
  }, []);

  const handleOpenDashboard = useCallback(() => {
    setIsDashboardOpen(true);
  }, []);

  const handleCloseDashboard = useCallback(() => {
    setIsDashboardOpen(false);
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Header */}
      <Header onOpenDashboard={handleOpenDashboard} />

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          onStartHunt={handleStartHunt}
          isLoading={isLoading}
          location={location}
          latitude={center.lat}
          longitude={center.lon}
          onLocationChange={handleLocationChange}
        />

        {/* Main Content */}
        <MainContent
          segments={segments}
          selectedSegment={selectedSegment}
          centerLat={center.lat}
          centerLon={center.lon}
          radiusKm={huntParams?.radiusKm ?? 10}
          isLoading={isLoading}
          isLoadingDetails={isLoadingDetails}
          onSegmentSelect={handleSegmentSelect}
          onClearSelection={clearSelection}
          onCenterChange={handleCenterChange}
        />
      </div>

      {/* User Dashboard */}
      <UserDashboard
        isOpen={isDashboardOpen}
        onClose={handleCloseDashboard}
        onSelectSegment={(id) => {
          selectSegment(id);
          setIsDashboardOpen(false);
        }}
      />

      {/* Login Prompt Toast */}
      {showLoginPrompt && (
        <div className="fixed bottom-4 right-4 bg-orange-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-3">
          <p className="text-sm font-medium">Log in with Strava to start hunting</p>
          <button
            onClick={login}
            className="text-sm font-semibold underline hover:text-orange-100"
          >
            Log in
          </button>
          <button
            onClick={() => setShowLoginPrompt(false)}
            aria-label="Dismiss"
            className="text-sm font-semibold hover:text-orange-100"
          >
            ✕
          </button>
        </div>
      )}

      {/* Error Toast */}
      {!showLoginPrompt && error && (
        <div className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}
    </div>
  );
}

export default function HomePage() {
  return <HomePageContent />;
}
