"use client";

/**
 * Hook for lazily loading the athlete's training heatmap.
 *
 * Nothing is fetched until `load()` is called (i.e. when the overlay is turned
 * on), keeping us well within Strava's rate limits. Results are cached per
 * sport so toggling the filter back and forth doesn't refetch.
 */

import { useState, useRef, useCallback } from "react";
import type { HeatmapResponse } from "@/types";
import { athletes, ApiError } from "@/lib/api";

/** Normalize the optional sport filter into a stable cache key. */
function sportKey(sport?: string): string {
  return sport && sport.length > 0 ? sport : "all";
}

/** Map API errors to user-facing (French) messages. */
function toErrorMessage(err: unknown): string {
  if (err instanceof ApiError && err.status === 401) {
    return "Session expirée - reconnectez-vous avec Strava";
  }
  return err instanceof Error
    ? err.message
    : "Impossible de charger la heatmap";
}

interface UseHeatmapReturn {
  points: [number, number][];
  activityCount: number;
  isLoading: boolean;
  error: string | null;
  /** Fetch (or serve from cache) the heatmap for the given sport filter. */
  load: (sport?: string) => Promise<void>;
  /** Reset state and abandon any in-flight request. */
  clear: () => void;
}

export function useHeatmap(): UseHeatmapReturn {
  const [points, setPoints] = useState<[number, number][]>([]);
  const [activityCount, setActivityCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cache previously fetched results per sport so switching the filter (or the
  // overlay) back to a sport we've already loaded doesn't hit Strava again.
  const cacheRef = useRef<Map<string, HeatmapResponse>>(new Map());
  // Monotonic request token so a slow in-flight request can't overwrite the
  // result of a newer one (last call wins).
  const requestIdRef = useRef(0);

  const load = useCallback(async (sport?: string) => {
    const key = sportKey(sport);

    // Serve from cache when we already have this sport's points.
    const cached = cacheRef.current.get(key);
    if (cached) {
      requestIdRef.current++; // supersede any in-flight request
      setPoints(cached.points);
      setActivityCount(cached.activity_count);
      setError(null);
      setIsLoading(false);
      return;
    }

    const requestId = ++requestIdRef.current;
    setIsLoading(true);
    setError(null);

    try {
      const response = await athletes.getHeatmap(sport ? { sport } : undefined);
      cacheRef.current.set(key, response);
      // Ignore if a newer load()/clear() superseded this request.
      if (requestId !== requestIdRef.current) return;
      setPoints(response.points);
      setActivityCount(response.activity_count);
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      console.error("Heatmap load failed:", err);
      setError(toErrorMessage(err));
      setPoints([]);
      setActivityCount(0);
    } finally {
      if (requestId === requestIdRef.current) {
        setIsLoading(false);
      }
    }
  }, []);

  const clear = useCallback(() => {
    // Bump the token so any in-flight request is ignored when it resolves.
    requestIdRef.current++;
    setPoints([]);
    setActivityCount(0);
    setError(null);
    setIsLoading(false);
  }, []);

  return { points, activityCount, isLoading, error, load, clear };
}
