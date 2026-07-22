"use client";

/**
 * Statistics summary component showing athlete totals
 */

import type { AthleteStats, ActivityTotals } from "@/types";

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
  colorClass = "text-primary" 
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
      {subValue && (
        <p className="text-xs text-subtle-green mt-1">{subValue}</p>
      )}
    </div>
  );
}

function TotalsSection({ 
  title, 
  totals, 
  icon,
  colorClass 
}: { 
  title: string; 
  totals: ActivityTotals;
  icon: string;
  colorClass: string;
}) {
  return (
    <div className="bg-surface rounded-xl p-4 border border-border">
      <div className="flex items-center gap-2 mb-3">
        <span className={`material-symbols-outlined ${colorClass}`}>{icon}</span>
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
          <p className="text-lg font-bold">{formatDistance(totals.elevation_gain)}</p>
          <p className="text-xs text-subtle-green">D+</p>
        </div>
      </div>
    </div>
  );
}

export function StatsSummary({ stats, isLoading }: StatsSummaryProps) {
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

      {/* Statistiques récentes (4 semaines) */}
      {stats.recent_ride_totals && (
        <TotalsSection
          title="Vélo (4 semaines)"
          totals={stats.recent_ride_totals}
          icon="directions_bike"
          colorClass="text-primary"
        />
      )}

      {stats.recent_run_totals && stats.recent_run_totals.count > 0 && (
        <TotalsSection
          title="Course (4 semaines)"
          totals={stats.recent_run_totals}
          icon="directions_run"
          colorClass="text-pink-500"
        />
      )}

      {/* Statistiques annuelles */}
      {stats.ytd_ride_totals && (
        <TotalsSection
          title="Vélo (cette année)"
          totals={stats.ytd_ride_totals}
          icon="calendar_today"
          colorClass="text-green-500"
        />
      )}

      {/* Statistiques all-time */}
      {stats.all_ride_totals && (
        <TotalsSection
          title="Vélo (tout temps)"
          totals={stats.all_ride_totals}
          icon="history"
          colorClass="text-purple-500"
        />
      )}
    </div>
  );
}
