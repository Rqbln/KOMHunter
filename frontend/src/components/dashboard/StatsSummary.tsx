"use client";

/**
 * Statistics summary component showing athlete totals.
 *
 * Cycling and running totals are shown side-by-side behind a Vélo/Course
 * toggle: each sport has its own recent (4-week), year-to-date and all-time
 * sections, coloured with the sport accent (orange for riding, blue for
 * running). Run sections only render when their totals report activity.
 */

import { useState } from "react";
import type { AthleteStats, ActivityTotals, ActivityType } from "@/types";
import { sportColorVar } from "@/lib/sport";

interface StatsSummaryProps {
  stats: AthleteStats | null;
  isLoading?: boolean;
}

function formatDistance(meters: number): string {
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(0)} km`;
  }
  return `${meters.toFixed(0)} m`;
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    return `${days}j ${remainingHours}h`;
  }

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }

  return `${minutes}m`;
}

function StatCard({
  icon,
  label,
  value,
  subValue,
  colorClass = "text-primary",
}: {
  icon: string;
  label: string;
  value: string;
  subValue?: string;
  colorClass?: string;
}) {
  return (
    <div className="bg-border/30 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className={`material-symbols-outlined ${colorClass}`}>{icon}</span>
        <span className="text-xs text-subtle-green">{label}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
      {subValue && <p className="text-xs text-subtle-green mt-1">{subValue}</p>}
    </div>
  );
}

function TotalsSection({
  title,
  totals,
  icon,
  accentColor,
}: {
  title: string;
  totals: ActivityTotals;
  icon: string;
  /** CSS color (accepts a var()) for the section's sport accent. */
  accentColor: string;
}) {
  return (
    <div
      className="bg-surface rounded-xl p-4 border-l-4 border-border"
      style={{ borderLeftColor: accentColor }}
    >
      <div className="flex items-center gap-2 mb-3">
        <span
          className="material-symbols-outlined"
          style={{ color: accentColor }}
        >
          {icon}
        </span>
        <h4 className="font-bold text-sm">{title}</h4>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-lg font-bold">{totals.count}</p>
          <p className="text-xs text-subtle-green">Activités</p>
        </div>
        <div>
          <p className="text-lg font-bold">{formatDistance(totals.distance)}</p>
          <p className="text-xs text-subtle-green">Distance</p>
        </div>
        <div>
          <p className="text-lg font-bold">{formatDuration(totals.moving_time)}</p>
          <p className="text-xs text-subtle-green">Temps</p>
        </div>
        <div>
          <p className="text-lg font-bold">
            {formatDistance(totals.elevation_gain)}
          </p>
          <p className="text-xs text-subtle-green">D+</p>
        </div>
      </div>
    </div>
  );
}

/** Sport toggle button used to switch between the Vélo and Course views. */
function SportToggleButton({
  sport,
  label,
  icon,
  active,
  disabled,
  onClick,
}: {
  sport: ActivityType;
  label: string;
  icon: string;
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={active}
      className={`flex h-full grow items-center justify-center gap-2 rounded-full px-2 text-sm font-bold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40 ${
        active ? "text-white shadow-sm" : "text-subtle-green"
      }`}
      style={active ? { backgroundColor: sportColorVar(sport) } : undefined}
    >
      <span className="material-symbols-outlined text-lg">{icon}</span>
      {label}
    </button>
  );
}

export function StatsSummary({ stats, isLoading }: StatsSummaryProps) {
  const [sport, setSport] = useState<ActivityType>("riding");

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-border/30 rounded-xl p-4 animate-pulse">
              <div className="h-4 bg-border rounded w-20 mb-2" />
              <div className="h-8 bg-border rounded w-16" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-8 text-subtle-green">
        <span className="material-symbols-outlined text-4xl mb-2">analytics</span>
        <p>Connectez-vous pour voir vos statistiques</p>
      </div>
    );
  }

  const rideColor = sportColorVar("riding");
  const runColor = sportColorVar("running");

  const hasRunData =
    (stats.recent_run_totals?.count ?? 0) > 0 ||
    (stats.ytd_run_totals?.count ?? 0) > 0 ||
    (stats.all_run_totals?.count ?? 0) > 0;

  // If there is no run data at all, keep the view pinned to cycling.
  const activeSport = !hasRunData ? "riding" : sport;

  return (
    <div className="space-y-4">
      {/* Records personnels */}
      <div className="grid grid-cols-2 gap-3">
        {stats.biggest_ride_distance && (
          <StatCard
            icon="straighten"
            label="Plus longue sortie"
            value={formatDistance(stats.biggest_ride_distance)}
            colorClass="text-blue-500"
          />
        )}
        {stats.biggest_climb_elevation_gain && (
          <StatCard
            icon="landscape"
            label="Plus gros dénivelé"
            value={formatDistance(stats.biggest_climb_elevation_gain)}
            colorClass="text-orange-500"
          />
        )}
      </div>

      {/* Vélo / Course toggle */}
      <div className="flex h-11 w-full items-center justify-center rounded-full border border-border bg-background p-1">
        <SportToggleButton
          sport="riding"
          label="Vélo"
          icon="directions_bike"
          active={activeSport === "riding"}
          onClick={() => setSport("riding")}
        />
        <SportToggleButton
          sport="running"
          label="Course"
          icon="directions_run"
          active={activeSport === "running"}
          disabled={!hasRunData}
          onClick={() => setSport("running")}
        />
      </div>

      {/* Cycling sections */}
      {activeSport === "riding" && (
        <div className="space-y-4">
          {stats.recent_ride_totals && (
            <TotalsSection
              title="Vélo (4 semaines)"
              totals={stats.recent_ride_totals}
              icon="directions_bike"
              accentColor={rideColor}
            />
          )}
          {stats.ytd_ride_totals && (
            <TotalsSection
              title="Vélo (cette année)"
              totals={stats.ytd_ride_totals}
              icon="calendar_today"
              accentColor={rideColor}
            />
          )}
          {stats.all_ride_totals && (
            <TotalsSection
              title="Vélo (tout temps)"
              totals={stats.all_ride_totals}
              icon="history"
              accentColor={rideColor}
            />
          )}
        </div>
      )}

      {/* Running sections */}
      {activeSport === "running" && (
        <div className="space-y-4">
          {stats.recent_run_totals && stats.recent_run_totals.count > 0 && (
            <TotalsSection
              title="Course (4 semaines)"
              totals={stats.recent_run_totals}
              icon="directions_run"
              accentColor={runColor}
            />
          )}
          {stats.ytd_run_totals && stats.ytd_run_totals.count > 0 && (
            <TotalsSection
              title="Course (cette année)"
              totals={stats.ytd_run_totals}
              icon="calendar_today"
              accentColor={runColor}
            />
          )}
          {stats.all_run_totals && stats.all_run_totals.count > 0 && (
            <TotalsSection
              title="Course (tout temps)"
              totals={stats.all_run_totals}
              icon="history"
              accentColor={runColor}
            />
          )}
        </div>
      )}
    </div>
  );
}
