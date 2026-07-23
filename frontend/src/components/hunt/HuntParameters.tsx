"use client";

/**
 * Hunt parameters form component.
 *
 * The single hunt form on "/": the simple explore controls (location, sport,
 * radius, max segments, sort, reliable-only) plus a collapsible "Filtres
 * avancés" panel carrying the WS-A backend filters (climb-category min/max,
 * average-grade min/max, distance min/max). On submit it emits an extended
 * {@link HuntParamsType} with the optional advanced fields, which useSegments
 * maps onto a SegmentExploreRequest.
 */

import { useState, useCallback, useMemo } from "react";
import { LocationInput } from "./LocationInput";
import { SportTypeToggle } from "./SportTypeToggle";
import { RadiusSlider } from "./RadiusSlider";
import { SortSelector } from "./SortSelector";
import { useSettings } from "@/hooks";
import { getClimbCategoryLabel } from "@/lib/utils";
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
  // Emitted on every radius-slider move (not just on submit) so the page can
  // update the map's radius circle live while the user drags.
  onRadiusChange?: (km: number) => void;
}

/** Climb-category select options: ordinal 0..5 -> NC / Cat 4 .. HC. */
const CLIMB_CATEGORIES = [0, 1, 2, 3, 4, 5] as const;

/** Parse a numeric text field, returning undefined for blank/invalid input. */
function toOptionalNumber(value: string): number | undefined {
  if (value.trim() === "") return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function HuntParameters({
  onSubmit,
  isLoading,
  location,
  latitude,
  longitude,
  onLocationChange,
  onRadiusChange,
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

  // Advanced filters (collapsed by default to keep the sidebar compact).
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [minCat, setMinCat] = useState(0);
  const [maxCat, setMaxCat] = useState(5);
  const [minGrade, setMinGrade] = useState("");
  const [maxGrade, setMaxGrade] = useState("");
  const [minDistanceKm, setMinDistanceKm] = useState("");
  const [maxDistanceKm, setMaxDistanceKm] = useState("");

  const sportType = sportOverride ?? settings.defaultSport;
  const radiusKm = radiusOverride ?? settings.defaultRadiusKm;

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
      latitude,
      longitude,
      sportType,
      radiusKm,
      maxSegments,
      sortBy,
      reliableOnly,
      minCat,
      maxCat,
      minGrade: toOptionalNumber(minGrade),
      maxGrade: toOptionalNumber(maxGrade),
      minDistanceKm: toOptionalNumber(minDistanceKm),
      maxDistanceKm: toOptionalNumber(maxDistanceKm),
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
          onChange={(value) => {
            setRadiusOverride(value);
            onRadiusChange?.(value);
          }}
        />

        {/* Max Segments Slider */}
        <RadiusSlider
          label="Max Segments"
          value={maxSegments}
          min={10}
          max={50}
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

      {/* Advanced filters (collapsible; default closed) */}
      <div className="rounded-2xl border border-border bg-background/40">
        <button
          type="button"
          onClick={() => setShowAdvanced((prev) => !prev)}
          aria-expanded={showAdvanced}
          aria-controls="advanced-filters-panel"
          className="flex w-full items-center justify-between gap-2 px-4 py-3 cursor-pointer select-none"
        >
          <span className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-lg">
              tune
            </span>
            <span className="text-sm font-bold">Filtres avancés</span>
          </span>
          <span
            className={`material-symbols-outlined text-subtle-green transition-transform ${
              showAdvanced ? "rotate-180" : ""
            }`}
          >
            expand_more
          </span>
        </button>

        {showAdvanced && (
          <div id="advanced-filters-panel" className="space-y-5 px-4 pb-4">
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
        )}
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
