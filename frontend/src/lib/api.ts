/**
 * API client for KOMHunter backend
 */

import type {
  SegmentExploreRequest,
  SegmentExploreResponse,
  SegmentDetails,
  AthleteProfile,
  AthleteStats,
  KOMsResponse,
  StarredSegmentsResponse,
  HeatmapResponse,
  GeocodingResult,
  GeocodeResponse,
  SessionTokenResponse,
  SessionInfo,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Error thrown for non-OK API responses, carrying the HTTP status code
 */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Base fetch wrapper with error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  // Normalize caller-supplied headers (may be a Headers, a [k,v][] or a record)
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  // Add auth token if available
  const token = typeof window !== "undefined"
    ? localStorage.getItem("kom_token")
    : null;

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // The backend transparently refreshes near-expiry Strava tokens and returns
  // a re-minted session JWT in this header — persist it for subsequent calls
  const refreshed = response.headers.get("X-KOM-Refreshed-Token");
  if (refreshed && typeof window !== "undefined") {
    localStorage.setItem("kom_token", refreshed);
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(error.detail || `API error: ${response.status}`, response.status);
  }

  return response.json();
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string }> {
  return fetchAPI("/api/health");
}

/**
 * Authentication
 */
export const auth = {
  /**
   * Get login URL to redirect user to Strava OAuth
   */
  getLoginUrl(redirectUrl?: string): string {
    const params = redirectUrl ? `?redirect_url=${encodeURIComponent(redirectUrl)}` : "";
    return `${API_BASE_URL}/api/auth/login${params}`;
  },
  
  /**
   * Exchange the current session JWT for a fresh one
   * (signature verified server-side, expiry check relaxed)
   */
  async refreshSession(token: string): Promise<SessionTokenResponse> {
    return fetchAPI("/api/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ token }),
    });
  },

  /**
   * Get current session info. The backend may transparently refresh a
   * near-expiry Strava token while serving this request, returning a
   * re-minted session JWT via the X-KOM-Refreshed-Token header.
   */
  async me(): Promise<SessionInfo> {
    return fetchAPI("/api/auth/me");
  },
};

/**
 * Segments API
 */
export const segments = {
  /**
   * Explore segments in a given area
   */
  async explore(params: SegmentExploreRequest): Promise<SegmentExploreResponse> {
    return fetchAPI("/api/segments/explore", {
      method: "POST",
      body: JSON.stringify(params),
    });
  },
  
  /**
   * Get segment details by ID
   */
  async getDetails(segmentId: number): Promise<SegmentDetails> {
    return fetchAPI(`/api/segments/${segmentId}`);
  },
};

/**
 * Athletes API
 */
export const athletes = {
  /**
   * Get current user's profile
   */
  async getProfile(): Promise<AthleteProfile> {
    return fetchAPI("/api/athletes/me");
  },
  
  /**
   * Get current user's statistics
   */
  async getStats(): Promise<AthleteStats> {
    return fetchAPI("/api/athletes/me/stats");
  },
  
  /**
   * Get current user's KOMs/QOMs
   */
  async getKOMs(page: number = 1, perPage: number = 30): Promise<KOMsResponse> {
    return fetchAPI(`/api/athletes/me/koms?page=${page}&per_page=${perPage}`);
  },
  
  /**
   * Get current user's starred segments
   */
  async getStarredSegments(page: number = 1, perPage: number = 30): Promise<StarredSegmentsResponse> {
    return fetchAPI(`/api/athletes/me/starred?page=${page}&per_page=${perPage}`);
  },
  
  /**
   * Get the current user's training heatmap: aggregated activity coordinates
   * ready to feed a Leaflet heat layer. All params are optional; when omitted
   * the backend aggregates across all sports and its default time window.
   * `sport` filters by discipline and must be a backend-recognized value
   * ("ride" | "run") — see lib/heatmapSport.ts; `after`/`before`
   * are Unix seconds; `max_activities` caps how many activities are scanned
   * (keep it economical — Strava is rate limited).
   */
  async getHeatmap(params?: {
    sport?: string;
    after?: number;
    before?: number;
    max_activities?: number;
  }): Promise<HeatmapResponse> {
    const query = new URLSearchParams();
    if (params?.sport) query.set("sport", params.sport);
    if (params?.after !== undefined) query.set("after", String(params.after));
    if (params?.before !== undefined) query.set("before", String(params.before));
    if (params?.max_activities !== undefined) {
      query.set("max_activities", String(params.max_activities));
    }
    const qs = query.toString();
    return fetchAPI(`/api/athletes/me/heatmap${qs ? `?${qs}` : ""}`);
  },
};

/**
 * Geocoding API
 */
export const geocoding = {
  /**
   * Fetch autocomplete suggestions for a location string.
   *
   * The backend answers 200 with `{ results: GeocodingResult[] }` — an empty
   * array for a blank query or no match, never a 4xx/5xx. This method reads the
   * `results` array and NEVER throws: any error (network failure, or an
   * unexpected non-200 that would make fetchAPI throw an ApiError) is swallowed
   * and reported as no suggestions, so partial typing can never surface an
   * error toast to the user.
   */
  async suggest(query: string): Promise<GeocodingResult[]> {
    const trimmed = query.trim();
    if (!trimmed) return [];
    try {
      const response = await fetchAPI<GeocodeResponse>(
        `/api/segments/geocode?query=${encodeURIComponent(trimmed)}`
      );
      return response.results ?? [];
    } catch {
      return [];
    }
  },
};

/**
 * Default export for convenience
 */
export default {
  healthCheck,
  auth,
  segments,
  athletes,
  geocoding,
};
