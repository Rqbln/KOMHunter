"use client";

/**
 * Hunt parameters form component
 */

import { useState, useCallback } from "react";
import { LocationInput } from "./LocationInput";
import { SportTypeToggle } from "./SportTypeToggle";
import { RadiusSlider } from "./RadiusSlider";
import type { HuntParameters as HuntParamsType, ActivityType } from "@/types";

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
  const [sportType, setSportType] = useState<ActivityType>("riding");
  const [radiusKm, setRadiusKm] = useState(25);
  const [maxSegments, setMaxSegments] = useState(50);

  const handleSubmit = useCallback(() => {
    onSubmit({
      location,
      latitude,
      longitude,
      sportType,
      radiusKm,
      maxSegments,
    });
  }, [location, latitude, longitude, sportType, radiusKm, maxSegments, onSubmit]);

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
        onChange={setSportType}
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
          onChange={setRadiusKm}
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
