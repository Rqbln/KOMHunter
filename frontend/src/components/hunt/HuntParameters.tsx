"use client";

/**
 * Hunt parameters form component
 */

import { useState, useCallback } from "react";
import { LocationInput } from "./LocationInput";
import { SportTypeToggle } from "./SportTypeToggle";
import { RadiusSlider } from "./RadiusSlider";
import { SortSelector } from "./SortSelector";
import { useSettings } from "@/hooks";
import type {
  HuntParameters as HuntParamsType,
  ActivityType,
  SegmentSortBy,
} from "@/types";

interface HuntParametersProps {
  onSubmit: (params: HuntParamsType) => void;
  isLoading?: boolean;
  // The search center is owned by the page so the map and this form stay in
  // sync: clicking the map recenters the search here too. Controlled inputs —
  // this component keeps no private copy of the location/coordinates.
  location: string;
  latitude: number;
  longitude: number;
  onLocationChange: (location: string, lat: number, lon: number) => void;
}

export function HuntParameters({
  onSubmit,
  isLoading,
  location,
  latitude,
  longitude,
  onLocationChange,
}: HuntParametersProps) {
  // Sport and radius are seeded from the user's saved defaults, falling back to
  // riding / 25 km when nothing is stored (or before settings hydrate). Rather
  // than copying settings into state via an effect, we track only the user's
  // in-form overrides and fall through to the saved default until they touch a
  // control — so the seed follows the persisted value without a setState effect.
  const { settings } = useSettings();
  const [sportOverride, setSportOverride] = useState<ActivityType | null>(null);
  const [radiusOverride, setRadiusOverride] = useState<number | null>(null);
  const [maxSegments, setMaxSegments] = useState(50);
  const [sortBy, setSortBy] = useState<SegmentSortBy>("difficulty");
  const [reliableOnly, setReliableOnly] = useState(false);

  const sportType = sportOverride ?? settings.defaultSport;
  const radiusKm = radiusOverride ?? settings.defaultRadiusKm;

  const handleSubmit = useCallback(() => {
    onSubmit({
      location,
      latitude,
      longitude,
      sportType,
      radiusKm,
      maxSegments,
      sortBy,
      reliableOnly,
    });
  }, [
    location,
    latitude,
    longitude,
    sportType,
    radiusKm,
    maxSegments,
    sortBy,
    reliableOnly,
    onSubmit,
  ]);

  return (
    <div className="space-y-6">
      {/* Location Input */}
      <LocationInput
        value={location}
        onChange={onLocationChange}
      />

      {/* Sport Type Toggle */}
      <SportTypeToggle
        value={sportType}
        onChange={(value) => setSportOverride(value)}
      />

      {/* Sliders */}
      <div className="space-y-6">
        {/* Radius Slider */}
        <RadiusSlider
          label="Search Radius"
          value={radiusKm}
          min={1}
          max={100}
          unit="km"
          onChange={(value) => setRadiusOverride(value)}
        />

        {/* Max Segments Slider */}
        <RadiusSlider
          label="Max Segments"
          value={maxSegments}
          min={10}
          max={200}
          unit=""
          onChange={setMaxSegments}
        />

        {/* Sort selector */}
        <SortSelector value={sortBy} onChange={setSortBy} />

        {/* Reliable-only filter */}
        <label className="flex items-start gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={reliableOnly}
            onChange={(e) => setReliableOnly(e.target.checked)}
            className="mt-0.5 size-4 accent-primary cursor-pointer"
          />
          <span className="text-sm">
            Segments fiables uniquement
            <span className="block text-xs text-subtle-green">
              Exclut les segments au temps KOM aberrant (erreur GPS)
            </span>
          </span>
        </label>
      </div>

      {/* Submit Button */}
      <div className="pt-4">
        <button
          onClick={handleSubmit}
          disabled={isLoading}
          className="flex w-full cursor-pointer items-center justify-center overflow-hidden rounded-full h-12 bg-primary hover:bg-primary-hover text-white text-base font-bold leading-normal tracking-[0.015em] shadow-lg shadow-primary/20 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <span className="mr-2 animate-spin material-symbols-outlined">
                progress_activity
              </span>
              Searching...
            </>
          ) : (
            <>
              <span className="mr-2 material-symbols-outlined">radar</span>
              Start Hunt
            </>
          )}
        </button>
      </div>
    </div>
  );
}
