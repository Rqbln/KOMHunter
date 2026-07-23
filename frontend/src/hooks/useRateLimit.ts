"use client";

/**
 * Hook exposing the latest captured Strava rate-limit usage.
 *
 * Polls GET /api/strava/rate-limit (which makes NO Strava call — it just reports
 * the usage the backend observed on prior responses) so the app-wide usage bar
 * can warn the user before they hit Strava's 100 req / 15 min limit.
 *
 * Economical by design:
 *  - only polls while the user is authenticated AND the tab is visible;
 *  - also refetches immediately on the "kom:ratelimit" window event, which
 *    fetchAPI dispatches on any 429, so a rate-limit hit surfaces at once.
 * SSR-safe: no window/interval work runs on the server.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useStrava } from "./useStrava";
import { strava } from "@/lib/api";
import type { RateLimitStatus } from "@/types";

// How often to refresh the usage snapshot while visible + authenticated.
const POLL_INTERVAL_MS = 20_000;

interface UseRateLimitReturn {
  status: RateLimitStatus | null;
  refresh: () => void;
}

export function useRateLimit(): UseRateLimitReturn {
  const { isAuthenticated } = useStrava();
  const [status, setStatus] = useState<RateLimitStatus | null>(null);

  // Guards against overlapping/lingering fetches updating state after unmount.
  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const refresh = useCallback(() => {
    strava
      .getRateLimit()
      .then((data) => {
        if (mountedRef.current) setStatus(data);
      })
      .catch(() => {
        // The bar is best-effort chrome; swallow errors (e.g. backend briefly
        // unreachable) rather than surfacing them.
      });
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || !isAuthenticated) return;

    let intervalId: ReturnType<typeof setInterval> | null = null;

    const startPolling = () => {
      if (intervalId !== null) return;
      refresh();
      intervalId = setInterval(refresh, POLL_INTERVAL_MS);
    };

    const stopPolling = () => {
      if (intervalId !== null) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };

    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        startPolling();
      } else {
        stopPolling();
      }
    };

    // Refetch right away on a 429 (dispatched by fetchAPI) so the cooldown shows.
    const handleRateLimitEvent = () => refresh();

    if (document.visibilityState === "visible") {
      startPolling();
    }
    document.addEventListener("visibilitychange", handleVisibility);
    window.addEventListener("kom:ratelimit", handleRateLimitEvent);

    return () => {
      stopPolling();
      document.removeEventListener("visibilitychange", handleVisibility);
      window.removeEventListener("kom:ratelimit", handleRateLimitEvent);
    };
  }, [isAuthenticated, refresh]);

  return { status, refresh };
}
