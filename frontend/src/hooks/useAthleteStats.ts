"use client";

/**
 * Hook for fetching and managing athlete statistics, KOMs, and starred segments
 */

import { useState, useCallback } from "react";
import type {
  AthleteStats,
  AthleteKOM,
  StarredSegment,
} from "@/types";
import { athletes } from "@/lib/api";

interface UseAthleteStatsReturn {
  stats: AthleteStats | null;
  koms: AthleteKOM[];
  starredSegments: StarredSegment[];
  isLoading: boolean;
  isLoadingKoms: boolean;
  isLoadingStarred: boolean;
  error: string | null;
  komsCount: number;
  starredCount: number;
  fetchStats: () => Promise<void>;
  fetchKOMs: (page?: number) => Promise<void>;
  fetchStarredSegments: (page?: number) => Promise<void>;
  fetchAll: () => Promise<void>;
}

export function useAthleteStats(): UseAthleteStatsReturn {
  // Stats state
  const [stats, setStats] = useState<AthleteStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // KOMs state
  const [koms, setKoms] = useState<AthleteKOM[]>([]);
  const [komsCount, setKomsCount] = useState(0);
  const [isLoadingKoms, setIsLoadingKoms] = useState(false);

  // Starred segments state
  const [starredSegments, setStarredSegments] = useState<StarredSegment[]>([]);
  const [starredCount, setStarredCount] = useState(0);
  const [isLoadingStarred, setIsLoadingStarred] = useState(false);
  
  // Error state
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await athletes.getStats();
      setStats(data);
    } catch (err) {
      console.error("Failed to fetch athlete stats:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch stats");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchKOMs = useCallback(async (page: number = 1) => {
    setIsLoadingKoms(true);
    setError(null);
    
    try {
      const response = await athletes.getKOMs(page);
      if (page === 1) {
        setKoms(response.koms);
      } else {
        setKoms(prev => [...prev, ...response.koms]);
      }
      setKomsCount(response.total_count);
    } catch (err) {
      console.error("Failed to fetch KOMs:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch KOMs");
    } finally {
      setIsLoadingKoms(false);
    }
  }, []);

  const fetchStarredSegments = useCallback(async (page: number = 1) => {
    setIsLoadingStarred(true);
    setError(null);
    
    try {
      const response = await athletes.getStarredSegments(page);
      if (page === 1) {
        setStarredSegments(response.segments);
      } else {
        setStarredSegments(prev => [...prev, ...response.segments]);
      }
      setStarredCount(response.total_count);
    } catch (err) {
      console.error("Failed to fetch starred segments:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch starred segments");
    } finally {
      setIsLoadingStarred(false);
    }
  }, []);

  const fetchAll = useCallback(async () => {
    await Promise.all([
      fetchStats(),
      fetchKOMs(),
      fetchStarredSegments(),
    ]);
  }, [fetchStats, fetchKOMs, fetchStarredSegments]);

  return {
    stats,
    koms,
    starredSegments,
    isLoading,
    isLoadingKoms,
    isLoadingStarred,
    error,
    komsCount,
    starredCount,
    fetchStats,
    fetchKOMs,
    fetchStarredSegments,
    fetchAll,
  };
}
