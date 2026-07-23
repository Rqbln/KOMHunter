"use client";

/**
 * KOMHunter Main Page
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { MainContent } from "@/components/layout/MainContent";
import { UserDashboard } from "@/components/dashboard/UserDashboard";
import { useSegments, useStrava, useHeatmap, useSettings } from "@/hooks";
import { heatmapSportParam } from "@/lib/heatmapSport";
import type { HuntParameters, HeatmapSport } from "@/types";

/** Human-readable label for a map-picked point (no reverse geocoding). */
function formatCoordLabel(lat: number, lon: number): string {
  return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
}

function HomePageContent() {
  // `center` is the single source of truth for the search area: it drives the
  // map view/radius circle AND feeds the sidebar form's coordinates, so a map
  // click and a "Start Hunt" agree on where to search. `location` is the label
  // shown in the form's text field for that same point.
  const [center, setCenter] = useState({ lat: 48.8566, lon: 2.3522 });
  const [location, setLocation] = useState("Paris, France");
  const [isDashboardOpen, setIsDashboardOpen] = useState(false);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  // Bumped on a logo reset to remount the hunt form, discarding its internal
  // sport/radius/filter overrides so it falls back to the saved defaults.
  const [resetKey, setResetKey] = useState(0);

  const { isAuthenticated, login } = useStrava();

  // The map/form start on the user's saved default location. `center`/`location`
  // are initialized to Paris (matching DEFAULT_SETTINGS) and re-seeded from the
  // saved default once it hydrates from localStorage — but only until the user
  // first picks a location / clicks the map / starts a hunt, after which their
  // choice must not be overwritten. A logo reset clears this flag (see below).
  const userMovedRef = useRef(false);

  // Live search radius, shared between the hunt form and the map's radius circle
  // so dragging the slider updates the circle immediately (before any submit).
  // Until the user touches the slider it follows the saved default (25 km when
  // nothing is stored) — mirroring the hunt form's own seeding logic.
  const { settings } = useSettings();
  const [radiusOverride, setRadiusOverride] = useState<number | null>(null);
  const radiusKm = radiusOverride ?? settings.defaultRadiusKm;

  // Seed the initial map/form location from the saved default once it hydrates
  // (useSettings starts at DEFAULT during hydration, then updates from
  // localStorage). Never override a location the user has already chosen.
  const { lat: defaultLat, lon: defaultLon, name: defaultName } =
    settings.defaultLocation;
  useEffect(() => {
    if (userMovedRef.current) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time sync of the persisted default into the controlled center before any user action
    setCenter({ lat: defaultLat, lon: defaultLon });
    setLocation(defaultName);
  }, [defaultLat, defaultLon, defaultName]);

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
    reset,
  } = useSegments();

  // Training-heatmap overlay state. Nothing is fetched until the user turns the
  // overlay on (useHeatmap.load is lazy), keeping us economical with Strava.
  const [heatmapEnabled, setHeatmapEnabled] = useState(false);
  const [heatmapSport, setHeatmapSport] = useState<HeatmapSport>("all");
  const {
    points: heatmapPoints,
    isLoading: isHeatmapLoading,
    load: loadHeatmap,
    clear: clearHeatmap,
  } = useHeatmap();

  // Toggle the overlay: turning it on triggers a (cached) load for the current
  // sport filter; turning it off clears the fetched points.
  const handleHeatmapToggle = useCallback(() => {
    setHeatmapEnabled((prev) => {
      const next = !prev;
      if (next) {
        loadHeatmap(heatmapSportParam(heatmapSport));
      } else {
        clearHeatmap();
      }
      return next;
    });
  }, [heatmapSport, loadHeatmap, clearHeatmap]);

  // Switching the sport filter refetches (or serves from cache) only while the
  // overlay is on.
  const handleHeatmapSportChange = useCallback(
    (sport: HeatmapSport) => {
      setHeatmapSport(sport);
      if (heatmapEnabled) {
        loadHeatmap(heatmapSportParam(sport));
      }
    },
    [heatmapEnabled, loadHeatmap]
  );

  const handleStartHunt = useCallback(
    async (params: HuntParameters) => {
      if (!isAuthenticated) {
        // No API call without a session: prompt the user to log in instead
        setShowLoginPrompt(true);
        return;
      }
      setShowLoginPrompt(false);
      userMovedRef.current = true;
      // params.latitude/longitude already come from `center` and params.radiusKm
      // matches the live `radiusKm` circle (both derive from the same seed), so
      // there is no need to re-sync the map here — just explore.
      await explore(params);
    },
    [explore, isAuthenticated]
  );

  // Geocoding / "my location" from the sidebar form updates the shared center.
  const handleLocationChange = useCallback(
    (newLocation: string, lat: number, lon: number) => {
      userMovedRef.current = true;
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
    userMovedRef.current = true;
    setCenter({ lat, lon: lng });
    setLocation(formatCoordLabel(lat, lng));
  }, []);

  const handleOpenDashboard = useCallback(() => {
    setIsDashboardOpen(true);
  }, []);

  const handleCloseDashboard = useCallback(() => {
    setIsDashboardOpen(false);
  }, []);

  // Logo reset: return the whole app to a fresh default menu using the user's
  // saved settings — recenter on the default location, drop back to the default
  // radius/sport, and clear every transient result, overlay, drawer and toast.
  const handleReset = useCallback(() => {
    const { defaultLocation } = settings;
    // Follow the saved default again (until the user next moves).
    userMovedRef.current = false;
    setCenter({ lat: defaultLocation.lat, lon: defaultLocation.lon });
    setLocation(defaultLocation.name);
    // null → radiusKm falls through to settings.defaultRadiusKm.
    setRadiusOverride(null);
    // Clear results (list, selection, count, error) and the heatmap overlay.
    reset();
    setHeatmapEnabled(false);
    setHeatmapSport("all");
    clearHeatmap();
    // Close drawers / dismiss toasts.
    setIsDashboardOpen(false);
    setShowLoginPrompt(false);
    // Remount the hunt form so its in-form overrides (sport/radius/filters)
    // reset to the saved defaults — a truly fresh menu.
    setResetKey((k) => k + 1);
  }, [settings, reset, clearHeatmap]);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Header */}
      <Header onOpenDashboard={handleOpenDashboard} onReset={handleReset} />

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          key={resetKey}
          onStartHunt={handleStartHunt}
          isLoading={isLoading}
          location={location}
          latitude={center.lat}
          longitude={center.lon}
          onLocationChange={handleLocationChange}
          onRadiusChange={setRadiusOverride}
        />

        {/* Main Content */}
        <MainContent
          segments={segments}
          selectedSegment={selectedSegment}
          centerLat={center.lat}
          centerLon={center.lon}
          radiusKm={radiusKm}
          viewResetKey={resetKey}
          isLoading={isLoading}
          isLoadingDetails={isLoadingDetails}
          onSegmentSelect={handleSegmentSelect}
          onClearSelection={clearSelection}
          onCenterChange={handleCenterChange}
          heatmapAvailable={isAuthenticated}
          heatmapEnabled={heatmapEnabled}
          heatmapSport={heatmapSport}
          isHeatmapLoading={isHeatmapLoading}
          heatmapPoints={heatmapEnabled ? heatmapPoints : []}
          onHeatmapToggle={handleHeatmapToggle}
          onHeatmapSportChange={handleHeatmapSportChange}
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
