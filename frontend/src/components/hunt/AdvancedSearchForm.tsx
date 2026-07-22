"use client";

/**
 * Advanced search form for the detailed /search page.
 *
 * Reuses the simple hunt controls (LocationInput / SportTypeToggle /
 * RadiusSlider) and layers on the WS-A backend filters: climb-category
 * min/max, average-grade min/max and distance min/max. On submit it emits an
 * extended {@link HuntParamsType} carrying the optional advanced fields, which
 * the page maps onto a SegmentExploreRequest.
 */

import { useCallback, useMemo, useState } from "react";
import { LocationInput } from "./LocationInput";
import { SportTypeToggle } from "./SportTypeToggle";
import { RadiusSlider } from "./RadiusSlider";
import { getClimbCategoryLabel } from "@/lib/utils";
import type { HuntParameters as HuntParamsType, ActivityType } from "@/types";

interface AdvancedSearchFormProps {
  onSubmit: (params: HuntParamsType) => void;
  isLoading?: boolean;
}

/** Climb-category select options: ordinal 0..5 -> NC / Cat 4 .. HC. */
const CLIMB_CATEGORIES = [0, 1, 2, 3, 4, 5] as const;

/** Parse a numeric text field, returning undefined for blank/invalid input. */
function toOptionalNumber(value: string): number | undefined {
  if (value.trim() === "") return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function AdvancedSearchForm({ onSubmit, isLoading }: AdvancedSearchFormProps) {
  const [location, setLocation] = useState("Paris, France");
  const [coordinates, setCoordinates] = useState({ lat: 48.8566, lon: 2.3522 });
  const [sportType, setSportType] = useState<ActivityType>("riding");
  const [radiusKm, setRadiusKm] = useState(25);
  const [maxSegments, setMaxSegments] = useState(50);

  // Advanced filters
  const [minCat, setMinCat] = useState(0);
  const [maxCat, setMaxCat] = useState(5);
  const [minGrade, setMinGrade] = useState("");
  const [maxGrade, setMaxGrade] = useState("");
  const [minDistanceKm, setMinDistanceKm] = useState("");
  const [maxDistanceKm, setMaxDistanceKm] = useState("");

  const handleLocationChange = useCallback(
    (newLocation: string, lat: number, lon: number) => {
      setLocation(newLocation);
      setCoordinates({ lat, lon });
    },
    []
  );

  // Keep the two category selects coherent: min never exceeds max and vice-versa.
  const handleMinCat = useCallback((value: number) => {
    setMinCat(value);
    setMaxCat((prev) => Math.max(prev, value));
  }, []);

  const handleMaxCat = useCallback((value: number) => {
    setMaxCat(value);
    setMinCat((prev) => Math.min(prev, value));
  }, []);

  const handleSubmit = useCallback(() => {
    onSubmit({
      location,
      latitude: coordinates.lat,
      longitude: coordinates.lon,
      sportType,
      radiusKm,
      maxSegments,
      minCat,
      maxCat,
      minGrade: toOptionalNumber(minGrade),
      maxGrade: toOptionalNumber(maxGrade),
      minDistanceKm: toOptionalNumber(minDistanceKm),
      maxDistanceKm: toOptionalNumber(maxDistanceKm),
    });
  }, [
    location,
    coordinates,
    sportType,
    radiusKm,
    maxSegments,
    minCat,
    maxCat,
    minGrade,
    maxGrade,
    minDistanceKm,
    maxDistanceKm,
    onSubmit,
  ]);

  const categoryOptions = useMemo(
    () =>
      CLIMB_CATEGORIES.map((cat) => ({
        value: cat,
        label: getClimbCategoryLabel(cat),
      })),
    []
  );

  return (
    <div className="space-y-6">
      {/* Location */}
      <LocationInput value={location} onChange={handleLocationChange} />

      {/* Sport type */}
      <SportTypeToggle value={sportType} onChange={setSportType} />

      {/* Area sliders */}
      <div className="space-y-6">
        <RadiusSlider
          label="Search Radius"
          value={radiusKm}
          min={1}
          max={100}
          unit="km"
          onChange={setRadiusKm}
        />
        <RadiusSlider
          label="Max Segments"
          value={maxSegments}
          min={10}
          max={200}
          unit=""
          onChange={setMaxSegments}
        />
      </div>

      {/* Advanced filters */}
      <div className="space-y-5 rounded-2xl border border-border bg-background/40 p-4">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-lg">tune</span>
          <h4 className="text-sm font-bold">Filtres avancés</h4>
        </div>

        {/* Climb category range */}
        <div className="space-y-2">
          <label className="text-sm font-medium leading-normal">
            Catégorie de montée
          </label>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <span className="text-xs text-subtle-green">Min</span>
              <select
                aria-label="Catégorie minimale"
                value={minCat}
                onChange={(e) => handleMinCat(Number(e.target.value))}
                className="w-full rounded-xl border border-border bg-background h-11 px-3 text-sm focus:outline-0 focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              >
                {categoryOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <span className="text-xs text-subtle-green">Max</span>
              <select
                aria-label="Catégorie maximale"
                value={maxCat}
                onChange={(e) => handleMaxCat(Number(e.target.value))}
                className="w-full rounded-xl border border-border bg-background h-11 px-3 text-sm focus:outline-0 focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              >
                {categoryOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Grade range */}
        <div className="space-y-2">
          <label className="text-sm font-medium leading-normal">
            Pente moyenne (%)
          </label>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <span className="text-xs text-subtle-green">Min</span>
              <input
                type="number"
                inputMode="decimal"
                step="0.5"
                placeholder="—"
                aria-label="Pente minimale"
                value={minGrade}
                onChange={(e) => setMinGrade(e.target.value)}
                className="w-full rounded-xl border border-border bg-background h-11 px-3 text-sm placeholder:text-subtle-green/60 focus:outline-0 focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              />
            </div>
            <div className="space-y-1">
              <span className="text-xs text-subtle-green">Max</span>
              <input
                type="number"
                inputMode="decimal"
                step="0.5"
                placeholder="—"
                aria-label="Pente maximale"
                value={maxGrade}
                onChange={(e) => setMaxGrade(e.target.value)}
                className="w-full rounded-xl border border-border bg-background h-11 px-3 text-sm placeholder:text-subtle-green/60 focus:outline-0 focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              />
            </div>
          </div>
        </div>

        {/* Distance range */}
        <div className="space-y-2">
          <label className="text-sm font-medium leading-normal">
            Distance (km)
          </label>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <span className="text-xs text-subtle-green">Min</span>
              <input
                type="number"
                inputMode="decimal"
                step="0.1"
                min="0"
                placeholder="—"
                aria-label="Distance minimale"
                value={minDistanceKm}
                onChange={(e) => setMinDistanceKm(e.target.value)}
                className="w-full rounded-xl border border-border bg-background h-11 px-3 text-sm placeholder:text-subtle-green/60 focus:outline-0 focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              />
            </div>
            <div className="space-y-1">
              <span className="text-xs text-subtle-green">Max</span>
              <input
                type="number"
                inputMode="decimal"
                step="0.1"
                min="0"
                placeholder="—"
                aria-label="Distance maximale"
                value={maxDistanceKm}
                onChange={(e) => setMaxDistanceKm(e.target.value)}
                className="w-full rounded-xl border border-border bg-background h-11 px-3 text-sm placeholder:text-subtle-green/60 focus:outline-0 focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Submit */}
      <div className="pt-2">
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
              Recherche...
            </>
          ) : (
            <>
              <span className="mr-2 material-symbols-outlined">travel_explore</span>
              Rechercher
            </>
          )}
        </button>
      </div>
    </div>
  );
}
