"use client";

/**
 * Location input with geocoding
 */

import { useState, useCallback, useEffect } from "react";
import { geocoding } from "@/lib/api";
import { debounce } from "@/lib/utils";

interface LocationInputProps {
  value: string;
  onChange: (location: string, lat: number, lon: number) => void;
}

export function LocationInput({ value, onChange }: LocationInputProps) {
  const [inputValue, setInputValue] = useState(value);
  const [isGeocoding, setIsGeocoding] = useState(false);

  // Reflect external changes to the location (e.g. a map click recentering the
  // search, or the resolved canonical name after geocoding) in the text field.
  useEffect(() => {
    setInputValue(value);
  }, [value]);
  const [isLocating, setIsLocating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounced geocoding function
  const geocodeLocation = useCallback(
    debounce(async (query: string) => {
      if (!query.trim()) return;

      setIsGeocoding(true);
      setError(null);

      try {
        const result = await geocoding.geocode(query);
        onChange(result.display_name, result.latitude, result.longitude);
      } catch (err) {
        console.error("Geocoding failed:", err);
        setError("Location not found");
      } finally {
        setIsGeocoding(false);
      }
    }, 500),
    [onChange]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    geocodeLocation(newValue);
  };

  const handleUseMyLocation = () => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setError("Géolocalisation non supportée par ce navigateur");
      return;
    }

    setIsLocating(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setInputValue("Ma position");
        onChange("Ma position", latitude, longitude);
        setIsLocating(false);
      },
      () => {
        setError("Impossible d'obtenir votre position");
        setIsLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium leading-normal">
        Target Location
      </label>
      <div className="relative">
        <input
          type="text"
          value={inputValue}
          onChange={handleChange}
          placeholder="City, region, or zip"
          className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-xl focus:outline-0 focus:ring-2 focus:ring-primary border border-border bg-background focus:border-primary h-12 pl-10 pr-4 placeholder:text-subtle-green/60 text-sm font-normal leading-normal transition-all"
        />
        <span className="material-symbols-outlined absolute left-3 top-3 text-subtle-green">
          {isGeocoding ? "progress_activity" : "location_on"}
        </span>
        {isGeocoding && (
          <span className="absolute right-3 top-3 text-subtle-green animate-spin material-symbols-outlined">
            progress_activity
          </span>
        )}
      </div>
      <button
        type="button"
        onClick={handleUseMyLocation}
        disabled={isLocating}
        className="flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary-hover disabled:opacity-60 transition-colors"
      >
        <span
          className={`material-symbols-outlined text-base leading-none ${
            isLocating ? "animate-spin" : ""
          }`}
        >
          {isLocating ? "progress_activity" : "my_location"}
        </span>
        {isLocating ? "Localisation..." : "Ma position"}
      </button>
      {error && (
        <p className="text-xs text-red-500">{error}</p>
      )}
    </div>
  );
}
