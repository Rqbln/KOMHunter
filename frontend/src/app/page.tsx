"use client";

/**
 * KOMHunter Main Page
 */

import { useState, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { MainContent } from "@/components/layout/MainContent";
import { UserDashboard } from "@/components/dashboard/UserDashboard";
import { useSegments, useStrava, StravaProvider } from "@/hooks";
import type { HuntParameters } from "@/types";

function HomePageContent() {
  const [huntParams, setHuntParams] = useState<HuntParameters | null>(null);
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
      setHuntParams(params);
      await explore(params);
    },
    [explore, isAuthenticated]
  );

  const handleSegmentSelect = useCallback(
    async (segmentId: number) => {
      await selectSegment(segmentId);
    },
    [selectSegment]
  );

  const handleOpenDashboard = useCallback(() => {
    setIsDashboardOpen(true);
  }, []);

  const handleCloseDashboard = useCallback(() => {
    setIsDashboardOpen(false);
  }, []);

  return (
    <>
      {/* Header */}
      <Header onOpenDashboard={handleOpenDashboard} />

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar onStartHunt={handleStartHunt} isLoading={isLoading} />

        {/* Main Content */}
        <MainContent
          segments={segments}
          selectedSegment={selectedSegment}
          centerLat={huntParams?.latitude ?? 48.8566}
          centerLon={huntParams?.longitude ?? 2.3522}
          radiusKm={huntParams?.radiusKm ?? 10}
          isLoading={isLoading}
          isLoadingDetails={isLoadingDetails}
          onSegmentSelect={handleSegmentSelect}
          onClearSelection={clearSelection}
        />
      </div>

      {/* User Dashboard */}
      <UserDashboard
        isOpen={isDashboardOpen}
        onClose={handleCloseDashboard}
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
    </>
  );
}

export default function HomePage() {
  return (
    <StravaProvider>
      <HomePageContent />
    </StravaProvider>
  );
}
