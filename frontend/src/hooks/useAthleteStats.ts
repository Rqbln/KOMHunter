"use client";

/**
 * Hook for fetching and managing athlete statistics, KOMs, PRs, and starred segments
 */

import { useState, useCallback, useEffect } from "react";
import type {
  AthleteStats,
  AthleteKOM,
  SegmentEffort,
  StarredSegment,
} from "@/types";
import { athletes } from "@/lib/api";

interface UseAthleteStatsReturn {
  stats: AthleteStats | null;
  koms: AthleteKOM[];
  prs: SegmentEffort[];
  starredSegments: StarredSegment[];
  isLoading: boolean;
  isLoadingKoms: boolean;
  isLoadingPrs: boolean;
  isLoadingStarred: boolean;
  error: string | null;
  komsCount: number;
  prsCount: number;
  starredCount: number;
  fetchStats: () => Promise<void>;
  fetchKOMs: (page?: number) => Promise<void>;
  fetchPRs: (page?: number) => Promise<void>;
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
  
  // PRs state
  const [prs, setPrs] = useState<SegmentEffort[]>([]);
  const [prsCount, setPrsCount] = useState(0);
  const [isLoadingPrs, setIsLoadingPrs] = useState(false);
  
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

  const fetchPRs = useCallback(async (page: number = 1) => {
    setIsLoadingPrs(true);
    setError(null);
    
    try {
      const response = await athletes.getPRs(page);
      if (page === 1) {
        setPrs(response.prs);
      } else {
        setPrs(prev => [...prev, ...response.prs]);
      }
      setPrsCount(response.total_count);
    } catch (err) {
      console.error("Failed to fetch PRs:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch PRs");
    } finally {
      setIsLoadingPrs(false);
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
      fetchPRs(),
      fetchStarredSegments(),
    ]);
  }, [fetchStats, fetchKOMs, fetchPRs, fetchStarredSegments]);

  return {
    stats,
    koms,
    prs,
    starredSegments,
    isLoading,
    isLoadingKoms,
    isLoadingPrs,
    isLoadingStarred,
    error,
    komsCount,
    prsCount,
    starredCount,
    fetchStats,
    fetchKOMs,
    fetchPRs,
    fetchStarredSegments,
    fetchAll,
  };
}
