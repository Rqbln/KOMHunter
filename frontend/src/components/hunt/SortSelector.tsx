"use client";

/**
 * "Trier par" selector shared by the simple hunt form and the advanced search
 * form. Picking a value only updates local form state; it is applied on the
 * next submit (same predictable "press the button to search" behavior as every
 * other control in these forms — no hidden auto-resubmit).
 *
 * The enriched sorts (popularity | competitiveness | opportunity) ask the
 * backend to fetch per-segment detail; the app's whole point is finding the
 * most FAMOUS and EASIEST-TO-WIN segments, so the copy spells out what each
 * ordering means.
 */

import type { SegmentSortBy } from "@/types";

interface SortSelectorProps {
  value: SegmentSortBy;
  onChange: (value: SegmentSortBy) => void;
}

const SORT_OPTIONS: { value: SegmentSortBy; label: string }[] = [
  { value: "difficulty", label: "Difficulté" },
  { value: "popularity", label: "Popularité" },
  { value: "competitiveness", label: "Compétitivité" },
  { value: "opportunity", label: "Opportunité" },
  { value: "distance", label: "Distance" },
  { value: "grade", label: "Pente" },
];

/** One-line explanation of the currently selected ordering. */
const SORT_HINTS: Record<SegmentSortBy, string> = {
  difficulty: "Terrain le plus facile d'abord",
  popularity: "Le plus fréquenté d'abord",
  competitiveness: "KOM le plus lent d'abord (plus facile à gagner)",
  opportunity: "Connu et gagnable",
  distance: "La plus courte d'abord",
  grade: "La plus raide d'abord",
};

export function SortSelector({ value, onChange }: SortSelectorProps) {
  return (
    <div className="space-y-2">
      <label
        htmlFor="sort-by"
        className="flex items-center gap-1.5 text-sm font-medium leading-normal"
      >
        <span className="material-symbols-outlined text-primary text-lg">sort</span>
        Trier par
      </label>
      <select
        id="sort-by"
        aria-label="Trier par"
        value={value}
        onChange={(e) => onChange(e.target.value as SegmentSortBy)}
        className="w-full rounded-xl border border-border bg-background h-11 px-3 text-sm focus:outline-0 focus:ring-2 focus:ring-primary focus:border-primary transition-all"
      >
        {SORT_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <p className="text-xs text-subtle-green">{SORT_HINTS[value]}</p>
    </div>
  );
}
