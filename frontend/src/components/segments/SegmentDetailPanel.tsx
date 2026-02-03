"use client";

/**
 * Segment detail panel - shows KOM/QOM and difficulty breakdown
 */

import type { SegmentDetails, DifficultyBreakdown } from "@/types";

interface SegmentDetailPanelProps {
  segment: SegmentDetails | null;
  isOpen: boolean;
  onClose: () => void;
}

function DifficultyBar({ 
  label, 
  value, 
  maxValue = 100,
  colorClass = "bg-primary"
}: { 
  label: string; 
  value: number;
  maxValue?: number;
  colorClass?: string;
}) {
  const percentage = Math.min(100, (value / maxValue) * 100);
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-subtle-green">{label}</span>
        <span className="font-medium">{value.toFixed(1)}</span>
      </div>
      <div className="h-2 bg-border rounded-full overflow-hidden">
        <div 
          className={`h-full ${colorClass} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function getCategoryConfig(category: string): { label: string; color: string; bgColor: string } {
  switch (category) {
    case "easy":
      return { label: "Facile", color: "text-green-600", bgColor: "bg-green-100" };
    case "moderate":
      return { label: "Modéré", color: "text-yellow-600", bgColor: "bg-yellow-100" };
    case "hard":
      return { label: "Difficile", color: "text-orange-600", bgColor: "bg-orange-100" };
    case "expert":
      return { label: "Expert", color: "text-red-600", bgColor: "bg-red-100" };
    default:
      return { label: "Inconnu", color: "text-gray-600", bgColor: "bg-gray-100" };
  }
}

function getClimbCategoryLabel(category: number): string {
  switch (category) {
    case 5: return "HC";
    case 1: return "Cat 1";
    case 2: return "Cat 2";
    case 3: return "Cat 3";
    case 4: return "Cat 4";
    default: return "NC";
  }
}

export function SegmentDetailPanel({ segment, isOpen, onClose }: SegmentDetailPanelProps) {
  if (!segment) return null;

  const categoryConfig = segment.difficulty_breakdown 
    ? getCategoryConfig(segment.difficulty_breakdown.category)
    : getCategoryConfig("moderate");

  return (
    <>
      {/* Backdrop */}
      <div 
        className={`fixed inset-0 bg-black/30 z-40 transition-opacity duration-300 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
      />
      
      {/* Panel */}
      <div 
        className={`fixed right-0 top-0 h-full w-full max-w-md bg-surface z-50 shadow-2xl transform transition-transform duration-300 ease-out overflow-hidden flex flex-col ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="size-10 rounded-full bg-primary/20 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary">landscape</span>
            </div>
            <div>
              <h2 className="font-bold text-lg leading-tight">{segment.name}</h2>
              <p className="text-xs text-subtle-green">
                {segment.city && `${segment.city}, `}{segment.state || segment.country}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="size-10 rounded-full hover:bg-border transition-colors flex items-center justify-center"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* KOM/QOM Section */}
          {segment.kom && (
            <section className="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-4">
              <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-lg">emoji_events</span>
                Records du Segment
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {segment.kom.kom_time && (
                  <div className="bg-surface rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-primary">{segment.kom.kom_time}</p>
                    <p className="text-xs text-subtle-green mt-1">KOM</p>
                  </div>
                )}
                {segment.kom.qom_time && (
                  <div className="bg-surface rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-pink-500">{segment.kom.qom_time}</p>
                    <p className="text-xs text-subtle-green mt-1">QOM</p>
                  </div>
                )}
              </div>
              {segment.kom.local_legend_name && (
                <div className="mt-3 pt-3 border-t border-border/50">
                  <p className="text-xs text-subtle-green">Légende Locale</p>
                  <p className="font-medium text-sm">{segment.kom.local_legend_name}</p>
                  {segment.kom.local_legend_efforts && (
                    <p className="text-xs text-subtle-green">{segment.kom.local_legend_efforts}</p>
                  )}
                </div>
              )}
            </section>
          )}
          
          {/* Difficulty Breakdown Section */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <span className="material-symbols-outlined text-lg">speed</span>
                Analyse de Difficulté
              </h3>
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${categoryConfig.bgColor} ${categoryConfig.color}`}>
                {categoryConfig.label}
              </span>
            </div>
            
            {/* Overall Score */}
            <div className="bg-border/30 rounded-xl p-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-subtle-green">Score Global</span>
                <span className="text-3xl font-bold">
                  {segment.difficulty_breakdown?.normalized_score.toFixed(1) || segment.difficulty_score.toFixed(1)}
                </span>
              </div>
              <div className="h-3 bg-border rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 via-yellow-500 via-orange-500 to-red-500"
                  style={{ 
                    width: `${segment.difficulty_breakdown?.normalized_score || segment.difficulty_score}%`,
                    transition: 'width 0.5s ease-out'
                  }}
                />
              </div>
              <div className="flex justify-between text-xs text-subtle-green mt-1">
                <span>Facile</span>
                <span>Expert</span>
              </div>
            </div>
            
            {/* Breakdown Bars */}
            {segment.difficulty_breakdown && (
              <div className="space-y-4">
                <DifficultyBar 
                  label="Difficulté Physique (terrain, altitude)" 
                  value={segment.difficulty_breakdown.physical_score}
                  colorClass="bg-blue-500"
                />
                <DifficultyBar 
                  label="Prestige (popularité, compétition)" 
                  value={segment.difficulty_breakdown.prestige_score}
                  colorClass="bg-purple-500"
                />
                <DifficultyBar 
                  label="Compétitivité (vitesse KOM)" 
                  value={segment.difficulty_breakdown.competitiveness_score}
                  colorClass="bg-orange-500"
                />
              </div>
            )}
            
            {/* Strava Category Points */}
            {segment.difficulty_breakdown && segment.difficulty_breakdown.strava_category_points > 0 && (
              <div className="mt-4 pt-4 border-t border-border">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-subtle-green">Score Catégorie Strava</span>
                  <span className="font-mono font-medium">
                    {segment.difficulty_breakdown.strava_category_points.toLocaleString()} pts
                  </span>
                </div>
                <p className="text-xs text-subtle-green mt-1">
                  (distance × pente = {(segment.distance / 1000).toFixed(1)}km × {segment.avg_grade.toFixed(1)}%)
                </p>
              </div>
            )}
          </section>
          
          {/* Statistics Section */}
          <section>
            <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-lg">analytics</span>
              Statistiques
            </h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-border/30 rounded-lg p-3 text-center">
                <p className="text-xl font-bold">{segment.effort_count.toLocaleString()}</p>
                <p className="text-xs text-subtle-green">Efforts</p>
              </div>
              <div className="bg-border/30 rounded-lg p-3 text-center">
                <p className="text-xl font-bold">{segment.athlete_count.toLocaleString()}</p>
                <p className="text-xs text-subtle-green">Athlètes</p>
              </div>
              <div className="bg-border/30 rounded-lg p-3 text-center">
                <p className="text-xl font-bold">{segment.star_count.toLocaleString()}</p>
                <p className="text-xs text-subtle-green">Favoris</p>
              </div>
            </div>
          </section>
          
          {/* Segment Details */}
          <section>
            <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-lg">info</span>
              Détails du Segment
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between py-2 border-b border-border/50">
                <span className="text-subtle-green">Distance</span>
                <span className="font-medium">{(segment.distance / 1000).toFixed(2)} km</span>
              </div>
              <div className="flex justify-between py-2 border-b border-border/50">
                <span className="text-subtle-green">Dénivelé</span>
                <span className="font-medium">{Math.round(segment.total_elevation_gain)} m</span>
              </div>
              <div className="flex justify-between py-2 border-b border-border/50">
                <span className="text-subtle-green">Pente moyenne</span>
                <span className="font-medium">{segment.avg_grade.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between py-2 border-b border-border/50">
                <span className="text-subtle-green">Pente max</span>
                <span className="font-medium">{segment.max_grade.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between py-2 border-b border-border/50">
                <span className="text-subtle-green">Altitude haute</span>
                <span className="font-medium">{Math.round(segment.elev_high)} m</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-subtle-green">Catégorie</span>
                <span className="font-medium">{getClimbCategoryLabel(segment.climb_category)}</span>
              </div>
            </div>
          </section>
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t border-border">
          <a
            href={`https://www.strava.com/segments/${segment.id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#FC4C02] hover:bg-[#E34402] text-white rounded-lg font-bold transition-colors"
          >
            <span className="material-symbols-outlined">open_in_new</span>
            Voir sur Strava
          </a>
        </div>
      </div>
    </>
  );
}
