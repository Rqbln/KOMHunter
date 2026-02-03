/**
 * TypeScript type definitions for KOMHunter
 */

// Activity types
export type ActivityType = "riding" | "running";

// Segment types
export interface SegmentSummary {
  id: number;
  name: string;
  distance: number;
  avg_grade: number;
  elev_difference: number;
  start_latlng: [number, number];
  end_latlng: [number, number];
  climb_category: number;
  difficulty_score: number;
}

export interface KOMData {
  kom_time?: string;
  qom_time?: string;
  overall_time?: string;
  kom_time_seconds?: number;
  qom_time_seconds?: number;
  local_legend_name?: string;
  local_legend_efforts?: string;
}

export interface DifficultyBreakdown {
  raw_score: number;
  normalized_score: number;
  category: DifficultyCategory;
  physical_score: number;
  prestige_score: number;
  competitiveness_score: number;
  strava_category_points: number;
  weights_used?: {
    physical: number;
    prestige: number;
    competitiveness: number;
  };
}

export interface SegmentDetails extends SegmentSummary {
  max_grade: number;
  elev_high: number;
  elev_low: number;
  total_elevation_gain: number;
  city: string;
  state: string;
  country: string;
  effort_count: number;
  athlete_count: number;
  star_count: number;
  polyline: string;
  difficulty_breakdown?: DifficultyBreakdown;
  kom?: KOMData;
}

// API request/response types
export interface SegmentExploreRequest {
  latitude: number;
  longitude: number;
  radius_km: number;
  activity_type: ActivityType;
  max_segments: number;
}

export interface SegmentExploreResponse {
  segments: SegmentSummary[];
  total_count: number;
  center_lat: number;
  center_lon: number;
  radius_km: number;
}

// Athlete types
export interface AthleteProfile {
  id: number;
  firstname: string;
  lastname: string;
  profile: string;
  profile_medium: string;
  city: string;
  state: string;
  country: string;
  sex: string;
  premium: boolean;
  created_at: string;
  updated_at: string;
}

export interface ActivityTotals {
  count: number;
  distance: number;
  moving_time: number;
  elapsed_time: number;
  elevation_gain: number;
  achievement_count?: number;
}

export interface AthleteStats {
  biggest_ride_distance?: number;
  biggest_climb_elevation_gain?: number;
  recent_ride_totals?: ActivityTotals;
  recent_run_totals?: ActivityTotals;
  ytd_ride_totals?: ActivityTotals;
  ytd_run_totals?: ActivityTotals;
  all_ride_totals?: ActivityTotals;
  all_run_totals?: ActivityTotals;
}

export interface AthleteKOM {
  segment_id: number;
  segment_name: string;
  activity_id: number;
  elapsed_time: number;
  elapsed_time_formatted: string;
  distance: number;
  avg_grade: number;
  start_date: string;
  start_date_local: string;
  kom_rank?: number;
}

export interface SegmentEffort {
  id: number;
  segment_id: number;
  segment_name: string;
  activity_id: number;
  elapsed_time: number;
  elapsed_time_formatted: string;
  moving_time: number;
  start_date: string;
  start_date_local: string;
  distance: number;
  pr_rank?: number;
  kom_rank?: number;
  achievements?: unknown[];
}

export interface StarredSegment {
  id: number;
  name: string;
  distance: number;
  avg_grade: number;
  elev_difference: number;
  climb_category: number;
  city: string;
  state: string;
  country: string;
  activity_type: string;
  starred_date: string;
  athlete_pr_effort?: unknown;
}

export interface KOMsResponse {
  koms: AthleteKOM[];
  total_count: number;
  page: number;
  per_page: number;
}

export interface StarredSegmentsResponse {
  segments: StarredSegment[];
  total_count: number;
  page: number;
  per_page: number;
}

export interface PRsResponse {
  prs: SegmentEffort[];
  total_count: number;
  page: number;
  per_page: number;
}

// Geocoding types
export interface GeocodingResult {
  latitude: number;
  longitude: number;
  display_name: string;
  type: string;
}

// Auth types
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_at: number;
  token_type: string;
}

// Hunt parameters
export interface HuntParameters {
  location: string;
  latitude: number;
  longitude: number;
  sportType: ActivityType;
  radiusKm: number;
  maxSegments: number;
}

// Difficulty categories
export type DifficultyCategory = "easy" | "moderate" | "hard" | "expert";

export interface DifficultyScore {
  raw_score: number;
  normalized_score: number;
  category: DifficultyCategory;
}
