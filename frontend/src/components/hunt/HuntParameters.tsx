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
}

export function HuntParameters({ onSubmit, isLoading }: HuntParametersProps) {
  const [location, setLocation] = useState("Paris, France");
  const [coordinates, setCoordinates] = useState({ lat: 48.8566, lon: 2.3522 });
  const [sportType, setSportType] = useState<ActivityType>("riding");
  const [radiusKm, setRadiusKm] = useState(25);
  const [maxSegments, setMaxSegments] = useState(50);

  const handleLocationChange = useCallback(
    (newLocation: string, lat: number, lon: number) => {
      setLocation(newLocation);
      setCoordinates({ lat, lon });
    },
    []
  );

  const handleSubmit = useCallback(() => {
    onSubmit({
      location,
      latitude: coordinates.lat,
      longitude: coordinates.lon,
      sportType,
      radiusKm,
      maxSegments,
    });
  }, [location, coordinates, sportType, radiusKm, maxSegments, onSubmit]);

  return (
    <div className="space-y-6">
      {/* Location Input */}
      <LocationInput
        value={location}
        onChange={handleLocationChange}
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
