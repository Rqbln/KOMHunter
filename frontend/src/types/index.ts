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
  athlete_name: string;
  elapsed_time: number;
  elapsed_time_formatted?: string;
  start_date?: string;
  athlete_id?: number;
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
