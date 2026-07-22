"use client";

/**
 * Strava authentication state, shared app-wide via React context.
 *
 * Mount <StravaProvider> once (see app/page.tsx) and consume with useStrava().
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from "react";
import type { AthleteProfile } from "@/types";
import { athletes, auth, ApiError } from "@/lib/api";
import { parseJwt, isTokenExpired } from "@/lib/utils";

interface StravaContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  athlete: AthleteProfile | null;
  error: string | null;
  login: () => void;
  logout: () => void;
}

const StravaContext = createContext<StravaContextValue | null>(null);

/**
 * Extract the OAuth callback JWT from the URL.
 * New backend contract puts it in the hash fragment ("#token=..."),
 * legacy links used a "?token=" query parameter.
 */
function extractCallbackToken(): string | null {
  const hash = window.location.hash;
  if (hash.length > 1) {
    const hashToken = new URLSearchParams(hash.slice(1)).get("token");
    if (hashToken) return hashToken;
  }
  return new URLSearchParams(window.location.search).get("token");
}

export function StravaProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [athlete, setAthlete] = useState<AthleteProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Handle OAuth callback token first: store it, clean the URL, reload
    const callbackToken = extractCallbackToken();
    if (callbackToken) {
      localStorage.setItem("kom_token", callbackToken);
      window.history.replaceState({}, "", window.location.pathname);
      window.location.reload();
      return;
    }

    const checkAuth = async () => {
      try {
        const token = localStorage.getItem("kom_token");

        if (!token) {
          setIsAuthenticated(false);
          setIsLoading(false);
          return;
        }

        // If the session JWT is near/past expiry, exchange it for a fresh one
        const payload = parseJwt(token);
        if (
          payload &&
          typeof payload.exp === "number" &&
          isTokenExpired(payload.exp)
        ) {
          const refreshed = await auth.refreshSession(token);
          localStorage.setItem("kom_token", refreshed.token);
        }

        // Validate the session by fetching the athlete profile
        const profile = await athletes.getProfile();
        setAthlete(profile);
        setIsAuthenticated(true);
        setError(null);
      } catch (err) {
        console.error("Auth check failed:", err);
        if (err instanceof ApiError && err.status === 401) {
          // Session genuinely rejected by the backend: clear it
          localStorage.removeItem("kom_token");
          setError(err.message);
        } else {
          // Network/server error: keep the token, do NOT log the user out
          setError("Backend unreachable");
        }
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = useCallback(() => {
    const currentUrl = window.location.href;
    window.location.href = auth.getLoginUrl(currentUrl);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("kom_token");
    setIsAuthenticated(false);
    setAthlete(null);
  }, []);

  const value = useMemo(
    () => ({ isAuthenticated, isLoading, athlete, error, login, logout }),
    [isAuthenticated, isLoading, athlete, error, login, logout]
  );

  return (
    <StravaContext.Provider value={value}>{children}</StravaContext.Provider>
  );
}

export function useStrava(): StravaContextValue {
  const context = useContext(StravaContext);
  if (!context) {
    throw new Error("useStrava must be used within a StravaProvider");
  }
  return context;
}
