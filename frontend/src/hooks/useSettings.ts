"use client";

/**
 * localStorage-backed user settings ("kom_settings").
 *
 * These are purely client-side preferences (default hunt sport/radius, unit
 * display, notification opt-ins). There is no server persistence — the store is
 * a thin, SSR-safe wrapper over localStorage.
 *
 * Implemented as an external store consumed via useSyncExternalStore so that:
 *   - the server render (and the hydrating client render) use the defaults,
 *     avoiding a hydration mismatch, then flip to the persisted values;
 *   - every component that calls useSettings() stays in sync when any of them
 *     calls update() — no context/provider needed;
 *   - no setState-in-effect is required.
 */

import { useSyncExternalStore, useCallback } from "react";
import type { ActivityType } from "@/types";

export type SettingsUnits = "metric" | "imperial";

/** A saved starting point for the map/hunt form and the logo-reset target. */
export interface DefaultLocation {
  name: string;
  lat: number;
  lon: number;
}

export interface Settings {
  /** Sport the hunt form starts on. */
  defaultSport: ActivityType;
  /** Search radius (km) the hunt form starts on. */
  defaultRadiusKm: number;
  /** City the map/hunt form centers on by default, and where the logo reset returns. */
  defaultLocation: DefaultLocation;
  /** Display units — stored preference only; no value conversion is applied yet. */
  units: SettingsUnits;
  /** Local opt-in for future KOM-opportunity alerts (no server push yet). */
  notifyKomOpportunities: boolean;
  /** Local opt-in for a future weekly summary (no server push yet). */
  notifyWeeklySummary: boolean;
}

const STORAGE_KEY = "kom_settings";

export const DEFAULT_SETTINGS: Settings = {
  defaultSport: "riding",
  defaultRadiusKm: 25,
  defaultLocation: { name: "Paris, France", lat: 48.8566, lon: 2.3522 },
  units: "metric",
  notifyKomOpportunities: true,
  notifyWeeklySummary: false,
};

/**
 * Read persisted settings, merged over the defaults. SSR-safe: returns the
 * defaults when there is no window (server render) or nothing stored.
 */
export function getSettings(): Settings {
  if (typeof window === "undefined") return DEFAULT_SETTINGS;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    const parsed = JSON.parse(raw) as Partial<Settings>;
    // Merge over defaults so a partial/older payload still yields every key.
    return { ...DEFAULT_SETTINGS, ...parsed };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

// Cached snapshot so getSnapshot() returns a STABLE reference between renders
// (useSyncExternalStore loops forever otherwise). Recomputed only when the
// stored value actually changes (via update() or a cross-tab storage event).
let snapshot: Settings = DEFAULT_SETTINGS;
let snapshotLoaded = false;
const listeners = new Set<() => void>();

function refreshSnapshot(): void {
  snapshot = getSettings();
  snapshotLoaded = true;
}

function getSnapshot(): Settings {
  if (!snapshotLoaded) refreshSnapshot();
  return snapshot;
}

function getServerSnapshot(): Settings {
  return DEFAULT_SETTINGS;
}

function subscribe(onStoreChange: () => void): () => void {
  listeners.add(onStoreChange);
  // Pick up edits made in another tab.
  const onStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY || event.key === null) {
      refreshSnapshot();
      onStoreChange();
    }
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(onStoreChange);
    window.removeEventListener("storage", onStorage);
  };
}

/** Merge a partial update into settings, persist it, and notify subscribers. */
export function updateSettings(partial: Partial<Settings>): void {
  const next: Settings = { ...getSnapshot(), ...partial };
  snapshot = next;
  snapshotLoaded = true;
  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // Ignore quota / private-mode write errors — preferences are non-critical.
    }
  }
  for (const listener of listeners) listener();
}

interface UseSettingsReturn {
  settings: Settings;
  /** Merge a partial update into settings and persist the result. */
  update: (partial: Partial<Settings>) => void;
}

export function useSettings(): UseSettingsReturn {
  const settings = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot
  );
  const update = useCallback((partial: Partial<Settings>) => {
    updateSettings(partial);
  }, []);
  return { settings, update };
}
