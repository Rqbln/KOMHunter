"use client";

/**
 * Hook for Strava authentication state
 */

import { useState, useEffect, useCallback } from "react";
import type { AthleteProfile } from "@/types";
import { athletes, auth } from "@/lib/api";
import { parseJwt, isTokenExpired } from "@/lib/utils";

interface UseStravaReturn {
  isAuthenticated: boolean;
  isLoading: boolean;
  athlete: AthleteProfile | null;
  error: string | null;
  login: () => void;
  logout: () => void;
}

export function useStrava(): UseStravaReturn {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [athlete, setAthlete] = useState<AthleteProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem("kom_token");
        
        if (!token) {
          setIsAuthenticated(false);
          setIsLoading(false);
          return;
        }

        // Parse token to check expiration (only for JWT tokens)
        const payload = parseJwt(token);
        
        // If token is a JWT and expired, try to refresh
        if (payload && isTokenExpired(payload.exp as number)) {
          const refreshToken = localStorage.getItem("kom_refresh_token");
          if (refreshToken) {
            try {
              const newTokens = await auth.refreshToken(refreshToken);
              localStorage.setItem("kom_token", newTokens.access_token);
              localStorage.setItem("kom_refresh_token", newTokens.refresh_token);
            } catch {
              // Refresh failed, clear tokens
              localStorage.removeItem("kom_token");
              localStorage.removeItem("kom_refresh_token");
              setIsAuthenticated(false);
              setIsLoading(false);
              return;
            }
          } else {
            // No refresh token, clear and redirect
            localStorage.removeItem("kom_token");
            setIsAuthenticated(false);
            setIsLoading(false);
            return;
          }
        }

        // Fetch athlete profile to validate token
        // This works for both JWT tokens and raw Strava access tokens
        const profile = await athletes.getProfile();
        setAthlete(profile);
        setIsAuthenticated(true);
      } catch (err) {
        console.error("Auth check failed:", err);
        // Token might be invalid, clear it
        localStorage.removeItem("kom_token");
        localStorage.removeItem("kom_refresh_token");
        setError(err instanceof Error ? err.message : "Authentication failed");
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Handle OAuth callback token
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    
    if (token) {
      localStorage.setItem("kom_token", token);
      // Clean URL
      window.history.replaceState({}, "", window.location.pathname);
      // Reload to trigger auth check
      window.location.reload();
    }
  }, []);

  const login = useCallback(() => {
    const currentUrl = window.location.href;
    window.location.href = auth.getLoginUrl(currentUrl);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("kom_token");
    localStorage.removeItem("kom_refresh_token");
    setIsAuthenticated(false);
    setAthlete(null);
  }, []);

  return {
    isAuthenticated,
    isLoading,
    athlete,
    error,
    login,
    logout,
  };
}
