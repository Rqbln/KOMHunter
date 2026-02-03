"use client";

/**
 * KOMHunter Main Page
 */

import { useState, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { MainContent } from "@/components/layout/MainContent";
import { UserDashboard } from "@/components/dashboard/UserDashboard";
import { useSegments } from "@/hooks";
import type { HuntParameters } from "@/types";

export default function HomePage() {
  const [huntParams, setHuntParams] = useState<HuntParameters | null>(null);
  const [isDashboardOpen, setIsDashboardOpen] = useState(false);
  
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
      setHuntParams(params);
      await explore(params);
    },
    [explore]
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

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}
    </>
  );
}
