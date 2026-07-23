"use client";

/**
 * KOMHunter — Detailed Search Page (/search)
 *
 * The advanced counterpart to the simple explore on "/". It reuses the shared
 * Strava auth context and the segment-selection side of useSegments, but runs
 * its own explore call so it can forward the WS-A advanced filters (climb
 * category, grade and distance bounds) that the simple form does not expose.
 */

import { useCallback, useState } from "react";
import { Header } from "@/components/layout/Header";
import { AdvancedSearchForm } from "@/components/hunt/AdvancedSearchForm";
import { SegmentMap } from "@/components/map/SegmentMap";
import { SegmentTable } from "@/components/segments/SegmentTable";
import { SegmentDetailPanel } from "@/components/segments/SegmentDetailPanel";
import { UserDashboard } from "@/components/dashboard/UserDashboard";
import { useSegments, useStrava } from "@/hooks";
import { segments as segmentsApi, ApiError } from "@/lib/api";
import type {
  HuntParameters,
  SegmentExploreRequest,
  SegmentSummary,
} from "@/types";

const DEFAULT_CENTER = { lat: 48.8566, lon: 2.3522 };
const DEFAULT_RADIUS_KM = 25;

/** Map API errors to user-facing messages (401 = expired session). */
function toErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError && err.status === 401) {
    return "Session expirée — reconnectez-vous avec Strava";
  }
  return err instanceof Error ? err.message : fallback;
}

/** Build the explore request body, omitting blank optional filters. */
function buildRequest(params: HuntParameters): SegmentExploreRequest {
  const request: SegmentExploreRequest = {
    latitude: params.latitude,
    longitude: params.longitude,
    radius_km: params.radiusKm,
    activity_type: params.sportType,
    max_segments: params.maxSegments,
    min_cat: params.minCat,
    max_cat: params.maxCat,
  };
  if (params.sortBy) request.sort_by = params.sortBy;
  if (params.reliableOnly) request.reliable_only = true;
  if (params.minGrade !== undefined) request.min_grade = params.minGrade;
  if (params.maxGrade !== undefined) request.max_grade = params.maxGrade;
  if (params.minDistanceKm !== undefined)
    request.min_distance_m = params.minDistanceKm * 1000;
  if (params.maxDistanceKm !== undefined)
    request.max_distance_m = params.maxDistanceKm * 1000;
  return request;
}

function SearchPageContent() {
  const { isAuthenticated, isLoading: isAuthLoading, login } = useStrava();

  // useSegments drives segment-detail selection (map highlight + side panel);
  // the results list itself is managed locally so advanced filters can be sent.
  const { selectedSegment, isLoadingDetails, selectSegment, clearSelection } =
    useSegments();

  const [results, setResults] = useState<SegmentSummary[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [center, setCenter] = useState(DEFAULT_CENTER);
  const [radiusKm, setRadiusKm] = useState(DEFAULT_RADIUS_KM);
  const [isDashboardOpen, setIsDashboardOpen] = useState(false);

  // Detail-panel close animation: keep the panel mounted for the 300ms slide-out
  // before clearing the selection (mirrors MainContent on the home page).
  const [closingSegmentId, setClosingSegmentId] = useState<number | null>(null);
  const isPanelOpen = !!selectedSegment && selectedSegment.id !== closingSegmentId;

  const handleSearch = useCallback(async (params: HuntParameters) => {
    setCenter({ lat: params.latitude, lon: params.longitude });
    setRadiusKm(params.radiusKm);
    setIsSearching(true);
    setError(null);

    try {
      const response = await segmentsApi.explore(buildRequest(params));
      setResults(response.segments);
    } catch (err) {
      console.error("Advanced search failed:", err);
      setError(toErrorMessage(err, "La recherche a échoué"));
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleSegmentSelect = useCallback(
    (segmentId: number) => {
      selectSegment(segmentId);
    },
    [selectSegment]
  );

  const handleClosePanel = useCallback(() => {
    const closingId = selectedSegment?.id ?? null;
    setClosingSegmentId(closingId);
    setTimeout(() => {
      clearSelection();
      setClosingSegmentId(null);
    }, 300);
  }, [selectedSegment, clearSelection]);

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header onOpenDashboard={() => setIsDashboardOpen(true)} />

      <main className="flex-1">
        {isAuthLoading ? (
          <div className="flex items-center justify-center py-32">
            <span className="material-symbols-outlined text-4xl text-subtle-green animate-spin">
              progress_activity
            </span>
          </div>
        ) : !isAuthenticated ? (
          <div className="flex items-center justify-center px-4 py-24">
            <div className="max-w-md w-full text-center rounded-2xl border border-border bg-surface p-8 shadow-sm">
              <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full bg-primary/15 text-primary">
                <span className="material-symbols-outlined text-3xl">
                  travel_explore
                </span>
              </div>
              <h1 className="text-xl font-bold">Recherche détaillée</h1>
              <p className="mt-2 text-sm text-subtle-green">
                Connectez-vous avec Strava pour filtrer les segments par
                catégorie de montée, pente et distance.
              </p>
              <button
                onClick={login}
                className="mt-6 inline-flex items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-bold text-black transition-colors hover:bg-primary-hover"
              >
                <span className="material-symbols-outlined text-lg">bolt</span>
                Se connecter avec Strava
              </button>
            </div>
          </div>
        ) : (
          <div className="mx-auto w-full max-w-7xl px-4 py-6 lg:px-6">
            {/* Page heading */}
            <div className="mb-6">
              <h1 className="text-2xl font-bold tracking-tight">
                Recherche détaillée
              </h1>
              <p className="mt-1 text-sm text-subtle-green">
                Affinez votre chasse au KOM avec des filtres de terrain avancés.
              </p>
            </div>

            <div className="grid items-start gap-6 lg:grid-cols-[360px_1fr]">
              {/* Filter form */}
              <aside className="lg:sticky lg:top-6">
                <div className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
                  <AdvancedSearchForm
                    onSubmit={handleSearch}
                    isLoading={isSearching}
                  />
                </div>
              </aside>

              {/* Results: map + sortable table */}
              <section className="min-w-0 space-y-6">
                <div className="relative h-[420px] overflow-hidden rounded-2xl border border-border shadow-sm">
                  <SegmentMap
                    segments={results}
                    selectedSegment={selectedSegment}
                    centerLat={center.lat}
                    centerLon={center.lon}
                    radiusKm={radiusKm}
                    onSegmentClick={handleSegmentSelect}
                  />
                  {isLoadingDetails && (
                    <div className="absolute right-4 top-4 z-[1000] flex items-center gap-2 rounded-lg bg-surface px-3 py-2 shadow-lg">
                      <div className="size-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                      <span className="text-sm">Chargement...</span>
                    </div>
                  )}
                </div>

                <div className="flex h-[600px] flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-sm">
                  <SegmentTable
                    segments={results}
                    isLoading={isSearching}
                    onSegmentClick={handleSegmentSelect}
                  />
                </div>
              </section>
            </div>
          </div>
        )}
      </main>

      {/* User Dashboard (left drawer) */}
      <UserDashboard
        isOpen={isDashboardOpen}
        onClose={() => setIsDashboardOpen(false)}
        onSelectSegment={(id) => {
          selectSegment(id);
          setIsDashboardOpen(false);
        }}
      />

      {/* Segment Detail Panel (right drawer) */}
      <SegmentDetailPanel
        segment={selectedSegment}
        isOpen={isPanelOpen}
        onClose={handleClosePanel}
      />

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-4 right-4 z-[1100] rounded-lg bg-red-500 px-4 py-2 text-white shadow-lg">
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return <SearchPageContent />;
}
