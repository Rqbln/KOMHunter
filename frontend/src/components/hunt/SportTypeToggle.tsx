"use client";

/**
 * Sport type toggle (Run/Ride)
 */

import type { ActivityType } from "@/types";

interface SportTypeToggleProps {
  value: ActivityType;
  onChange: (value: ActivityType) => void;
}

export function SportTypeToggle({ value, onChange }: SportTypeToggleProps) {
  return (
    <div className="space-y-3">
      <label className="text-sm font-medium leading-normal">Sport Type</label>
      <div className="flex h-12 w-full items-center justify-center rounded-full bg-background border border-border p-1">
        <label
          className={`flex cursor-pointer h-full grow items-center justify-center overflow-hidden rounded-full px-2 text-sm font-bold leading-normal transition-all duration-200 ${
            value === "running"
              ? "bg-primary shadow-sm text-black"
              : "text-subtle-green"
          }`}
        >
          <span className="flex items-center gap-2">
            <span className="material-symbols-outlined text-lg">
              directions_run
            </span>
            Run
          </span>
          <input
            type="radio"
            name="sport_type"
            value="running"
            checked={value === "running"}
            onChange={() => onChange("running")}
            className="invisible w-0 absolute"
          />
        </label>
        <label
          className={`flex cursor-pointer h-full grow items-center justify-center overflow-hidden rounded-full px-2 text-sm font-bold leading-normal transition-all duration-200 ${
            value === "riding"
              ? "bg-primary shadow-sm text-black"
              : "text-subtle-green"
          }`}
        >
          <span className="flex items-center gap-2">
            <span className="material-symbols-outlined text-lg">pedal_bike</span>
            Ride
          </span>
          <input
            type="radio"
            name="sport_type"
            value="riding"
            checked={value === "riding"}
            onChange={() => onChange("riding")}
            className="invisible w-0 absolute"
          />
        </label>
      </div>
    </div>
  );
}
