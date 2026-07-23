"use client";

/**
 * Hook for segment exploration and management
 */

import { useState, useCallback } from "react";
import type {
  SegmentSummary,
  SegmentDetails,
  SegmentExploreRequest,
  HuntParameters,
} from "@/types";
import { segments, ApiError } from "@/lib/api";

/** Map API errors to user-facing messages (401 = expired session) */
function toErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError && err.status === 401) {
    return "Session expired - log in with Strava again";
  }
  return err instanceof Error ? err.message : fallback;
}

interface UseSegmentsReturn {
  segments: SegmentSummary[];
  selectedSegment: SegmentDetails | null;
  isLoading: boolean;
  isLoadingDetails: boolean;
  error: string | null;
  totalCount: number;
  explore: (params: HuntParameters) => Promise<void>;
  selectSegment: (segmentId: number) => Promise<void>;
  clearSelection: () => void;
  reset: () => void;
}

export function useSegments(): UseSegmentsReturn {
  const [segmentList, setSegmentList] = useState<SegmentSummary[]>([]);
  const [selectedSegment, setSelectedSegment] = useState<SegmentDetails | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  const explore = useCallback(async (params: HuntParameters) => {
    setIsLoading(true);
    setError(null);

    try {
      const request: SegmentExploreRequest = {
        latitude: params.latitude,
        longitude: params.longitude,
        radius_km: params.radiusKm,
        activity_type: params.sportType,
        max_segments: params.maxSegments,
      };
      // Only forward an ordering when the form picked one; omitted lets the
      // backend apply its "difficulty" default.
      if (params.sortBy) request.sort_by = params.sortBy;
      if (params.reliableOnly) request.reliable_only = true;

      const response = await segments.explore(request);
      setSegmentList(response.segments);
      setTotalCount(response.total_count);
    } catch (err) {
      console.error("Segment exploration failed:", err);
      setError(toErrorMessage(err, "Failed to explore segments"));
      setSegmentList([]);
      setTotalCount(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const selectSegment = useCallback(async (segmentId: number) => {
    setIsLoadingDetails(true);
    setError(null);

    try {
      const details = await segments.getDetails(segmentId);
      setSelectedSegment(details);
    } catch (err) {
      console.error("Failed to load segment details:", err);
      setError(toErrorMessage(err, "Failed to load segment details"));
    } finally {
      setIsLoadingDetails(false);
    }
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedSegment(null);
  }, []);

  const reset = useCallback(() => {
    setSegmentList([]);
    setSelectedSegment(null);
    setTotalCount(0);
    setError(null);
  }, []);

  return {
    segments: segmentList,
    selectedSegment,
    isLoading,
    isLoadingDetails,
    error,
    totalCount,
    explore,
    selectSegment,
    clearSelection,
    reset,
  };
}
