/**
 * Utility functions for KOMHunter frontend
 */

import { type ClassValue, clsx } from "clsx";

/**
 * Merge class names with clsx (simplified version without tailwind-merge)
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

/**
 * Format seconds to time string (mm:ss or hh:mm:ss)
 */
export function formatTime(seconds: number): string {
  if (seconds < 0) return "0:00";
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }
  return `${minutes}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Format distance in meters to km or m
 */
export function formatDistance(meters: number): string {
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)} km`;
  }
  return `${Math.round(meters)} m`;
}

/**
 * Format elevation in meters
 */
export function formatElevation(meters: number): string {
  return `${Math.round(meters)} m`;
}

/**
 * Format grade as percentage
 */
export function formatGrade(grade: number): string {
  return `${grade.toFixed(1)}%`;
}

/**
 * Get difficulty category color
 */
export function getDifficultyColor(category: string): string {
  switch (category) {
    case "easy":
      return "text-green-500";
    case "moderate":
      return "text-yellow-500";
    case "hard":
      return "text-orange-500";
    case "expert":
      return "text-red-500";
    default:
      return "text-gray-500";
  }
}

/**
 * Get climb category label
 */
export function getClimbCategoryLabel(category: number): string {
  switch (category) {
    case 0:
      return "NC";
    case 1:
      return "Cat 4";
    case 2:
      return "Cat 3";
    case 3:
      return "Cat 2";
    case 4:
      return "Cat 1";
    case 5:
      return "HC";
    default:
      return "NC";
  }
}

/**
 * Debounce function
 */
export function debounce<Args extends unknown[]>(
  func: (...args: Args) => unknown,
  wait: number
): (...args: Args) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return (...args: Args) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Parse JWT token payload (without verification)
 */
export function parseJwt(token: string): Record<string, unknown> | null {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

/**
 * Check if token is expired
 */
export function isTokenExpired(expiresAt: number): boolean {
  // Add 5 minute buffer
  return Date.now() / 1000 > expiresAt - 300;
}

/**
 * Escape a string for safe interpolation into an HTML sink.
 *
 * Used for values that reach an innerHTML sink outside React's auto-escaping
 * (e.g. Leaflet popup content built from Strava-supplied segment names, which
 * are untrusted user-generated text).
 */
export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
