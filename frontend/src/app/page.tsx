"use client";

/**
 * KOMHunter Main Page
 */

import { useState, useCallback } from "react";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { MainContent } from "@/components/layout/MainContent";
import { useSegments } from "@/hooks";
import type { HuntParameters } from "@/types";

export default function HomePage() {
  const [huntParams, setHuntParams] = useState<HuntParameters | null>(null);
  const {
    segments,
    selectedSegment,
    isLoading,
    error,
    totalCount,
    explore,
    selectSegment,
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

  return (
    <>
      {/* Header */}
      <Header />

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
          onSegmentSelect={handleSegmentSelect}
        />
      </div>

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}
    </>
  );
}
