"use client";

/**
 * Location autocomplete input.
 *
 * As the user types (min 2 chars, debounced ~300ms) it fetches geocoding
 * suggestions from the backend and shows them in a dropdown. Nothing is applied
 * automatically: `onChange(display_name, lat, lon)` fires ONLY when the user
 * PICKS a suggestion (click / Enter) or uses the "Ma position" button. Partial
 * typing never triggers a navigation or surfaces an error toast — no match just
 * renders a subtle "Aucun résultat" row.
 */

import { useState, useEffect, useRef } from "react";
import { geocoding } from "@/lib/api";
import type { GeocodingResult } from "@/types";

interface LocationInputProps {
  value: string;
  onChange: (location: string, lat: number, lon: number) => void;
}

/** Minimum characters before we hit the geocoder. */
const MIN_QUERY_LENGTH = 2;
/** Debounce window for suggestion fetches. */
const DEBOUNCE_MS = 320;
/** Cap on how many suggestions we render. */
const MAX_SUGGESTIONS = 6;

export function LocationInput({ value, onChange }: LocationInputProps) {
  const [inputValue, setInputValue] = useState(value);
  // `query` drives suggestion fetching and is set ONLY by user typing — the
  // external `value` sync below deliberately does NOT touch it, so a map
  // recenter or a resolved name flowing back in never re-opens the dropdown.
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<GeocodingResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [highlight, setHighlight] = useState(-1);
  const [isLocating, setIsLocating] = useState(false);
  // Geolocation-only errors (the geocoder itself never errors — see api.ts).
  const [geoError, setGeoError] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // Reflect external changes to the location (a map click recentering the
  // search, or the resolved canonical name after a pick) in the text field.
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Debounced suggestion fetch, keyed on the typed query. The cancelled flag +
  // cleanup guarantee only the latest keystroke's results land in state.
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < MIN_QUERY_LENGTH) {
      setSuggestions([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    let cancelled = false;
    const timer = setTimeout(async () => {
      const results = await geocoding.suggest(trimmed);
      if (cancelled) return;
      setSuggestions(results.slice(0, MAX_SUGGESTIONS));
      setHighlight(-1);
      setIsLoading(false);
      setIsOpen(true);
    }, DEBOUNCE_MS);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  // Close the dropdown when the user clicks/taps outside the component.
  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setQuery(newValue);
    setGeoError(null);
    setIsOpen(newValue.trim().length >= MIN_QUERY_LENGTH);
  };

  const handleSelect = (item: GeocodingResult) => {
    setInputValue(item.display_name);
    setQuery(""); // prevent a re-fetch for the value we just applied
    setSuggestions([]);
    setHighlight(-1);
    setIsOpen(false);
    onChange(item.display_name, item.latitude, item.longitude);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || suggestions.length === 0) {
      if (e.key === "Escape") setIsOpen(false);
      return;
    }
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setHighlight((h) => (h + 1) % suggestions.length);
        break;
      case "ArrowUp":
        e.preventDefault();
        setHighlight((h) => (h - 1 + suggestions.length) % suggestions.length);
        break;
      case "Enter":
        if (highlight >= 0 && highlight < suggestions.length) {
          e.preventDefault();
          handleSelect(suggestions[highlight]);
        }
        break;
      case "Escape":
        setIsOpen(false);
        break;
    }
  };

  const handleUseMyLocation = () => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGeoError("Géolocalisation non supportée par ce navigateur");
      return;
    }

    setIsLocating(true);
    setGeoError(null);
    setIsOpen(false);
    setSuggestions([]);
    setQuery("");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setInputValue("Ma position");
        onChange("Ma position", latitude, longitude);
        setIsLocating(false);
      },
      () => {
        setGeoError("Impossible d'obtenir votre position");
        setIsLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const showNoResults =
    isOpen &&
    !isLoading &&
    suggestions.length === 0 &&
    query.trim().length >= MIN_QUERY_LENGTH;

  return (
    <div className="space-y-3" ref={containerRef}>
      <label className="text-sm font-medium leading-normal">
        Target Location
      </label>
      <div className="relative">
        <input
          type="text"
          value={inputValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (suggestions.length > 0) setIsOpen(true);
          }}
          placeholder="City, region, or zip"
          autoComplete="off"
          role="combobox"
          aria-expanded={isOpen}
          aria-autocomplete="list"
          aria-controls="location-suggestions"
          className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-xl focus:outline-0 focus:ring-2 focus:ring-primary border border-border bg-background focus:border-primary h-12 pl-10 pr-4 placeholder:text-subtle-green/60 text-sm font-normal leading-normal transition-all"
        />
        <span
          className={`material-symbols-outlined absolute left-3 top-3 text-subtle-green ${
            isLoading ? "animate-spin" : ""
          }`}
        >
          {isLoading ? "progress_activity" : "location_on"}
        </span>

        {(isOpen && (suggestions.length > 0 || showNoResults)) && (
          <ul
            id="location-suggestions"
            role="listbox"
            className="absolute left-0 right-0 top-full z-30 mt-1 max-h-64 overflow-y-auto rounded-xl border border-border bg-background py-1 shadow-lg shadow-black/10"
          >
            {suggestions.map((item, index) => (
              <li
                key={`${item.latitude},${item.longitude},${item.display_name}`}
                role="option"
                aria-selected={index === highlight}
                onMouseDown={(e) => {
                  // mousedown (not click) so selection wins the race against the
                  // input's blur firing the click-outside handler.
                  e.preventDefault();
                  handleSelect(item);
                }}
                onMouseEnter={() => setHighlight(index)}
                className={`flex cursor-pointer items-center gap-2 px-3 py-2 text-sm transition-colors ${
                  index === highlight
                    ? "bg-primary/10 text-primary"
                    : "hover:bg-primary/10"
                }`}
              >
                <span className="material-symbols-outlined text-base leading-none text-subtle-green">
                  location_on
                </span>
                <span className="truncate">{item.display_name}</span>
              </li>
            ))}
            {showNoResults && (
              <li className="px-3 py-2 text-sm text-subtle-green/70">
                Aucun résultat
              </li>
            )}
          </ul>
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
      {geoError && <p className="text-xs text-red-500">{geoError}</p>}
    </div>
  );
}
