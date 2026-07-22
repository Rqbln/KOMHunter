"use client";

/**
 * User dashboard component - shows stats, KOMs, PRs, and starred segments
 */

import { useState, useEffect } from "react";
import { useStrava, useAthleteStats } from "@/hooks";
import { StatsSummary } from "./StatsSummary";
import { KOMCard, PRCard, StarredSegmentCard } from "./KOMCard";

type TabType = "stats" | "koms" | "prs" | "starred";

interface UserDashboardProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectSegment?: (segmentId: number) => void;
}

export function UserDashboard({ isOpen, onClose, onSelectSegment }: UserDashboardProps) {
  const { athlete, isAuthenticated } = useStrava();
  const {
    stats,
    koms,
    prs,
    starredSegments,
    isLoading,
    isLoadingKoms,
    isLoadingPrs,
    isLoadingStarred,
    komsCount,
    prsCount,
    starredCount,
    fetchAll,
  } = useAthleteStats();

  const [activeTab, setActiveTab] = useState<TabType>("stats");

  // Fetch data when dashboard opens and user is authenticated
  useEffect(() => {
    if (isOpen && isAuthenticated) {
      fetchAll();
    }
  }, [isOpen, isAuthenticated, fetchAll]);

  const tabs: { id: TabType; label: string; icon: string; count?: number }[] = [
    { id: "stats", label: "Stats", icon: "analytics" },
    { id: "koms", label: "KOMs", icon: "emoji_events", count: komsCount },
    { id: "prs", label: "PRs", icon: "timer", count: prsCount },
    { id: "starred", label: "Favoris", icon: "star", count: starredCount },
  ];

  if (!isAuthenticated) {
    return null;
  }

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
        className={`fixed left-0 top-0 h-full w-full max-w-md bg-surface z-50 shadow-2xl transform transition-transform duration-300 ease-out overflow-hidden flex flex-col ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-3">
            {athlete?.profile && (
              <div
                className="size-12 rounded-full bg-cover bg-center border-2 border-primary"
                style={{ backgroundImage: `url("${athlete.profile}")` }}
              />
            )}
            <div>
              <h2 className="font-bold text-lg">{athlete?.firstname} {athlete?.lastname}</h2>
              <p className="text-xs text-subtle-green">
                {athlete?.city && `${athlete.city}, `}{athlete?.country}
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

        {/* Tabs */}
        <div className="flex border-b border-border">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3 px-2 text-sm font-medium transition-colors relative ${
                activeTab === tab.id
                  ? "text-primary"
                  : "text-subtle-green hover:text-foreground"
              }`}
            >
              <div className="flex items-center justify-center gap-1">
                <span className="material-symbols-outlined text-lg">{tab.icon}</span>
                <span className="hidden sm:inline">{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <span className="text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded-full">
                    {tab.count}
                  </span>
                )}
              </div>
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Stats Tab */}
          {activeTab === "stats" && (
            <StatsSummary stats={stats} isLoading={isLoading} />
          )}

          {/* KOMs Tab */}
          {activeTab === "koms" && (
            <div className="space-y-3">
              {isLoadingKoms ? (
                <div className="flex justify-center py-8">
                  <div className="size-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
              ) : koms.length > 0 ? (
                koms.map((kom) => (
                  <KOMCard
                    key={`${kom.segment_id}-${kom.activity_id}`}
                    kom={kom}
                    onClick={() => {
                      onSelectSegment?.(kom.segment_id);
                      onClose();
                    }}
                  />
                ))
              ) : (
                <div className="text-center py-8 text-subtle-green">
                  <span className="material-symbols-outlined text-4xl mb-2">emoji_events</span>
                  <p>Pas encore de KOM</p>
                  <p className="text-xs mt-1">Allez chercher vos couronnes!</p>
                </div>
              )}
            </div>
          )}

          {/* PRs Tab */}
          {activeTab === "prs" && (
            <div className="space-y-3">
              {isLoadingPrs ? (
                <div className="flex justify-center py-8">
                  <div className="size-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
              ) : prs.length > 0 ? (
                prs.map((pr) => (
                  <PRCard
                    key={pr.id}
                    pr={pr}
                    onClick={() => {
                      onSelectSegment?.(pr.segment_id);
                      onClose();
                    }}
                  />
                ))
              ) : (
                <div className="text-center py-8 text-subtle-green">
                  <span className="material-symbols-outlined text-4xl mb-2">timer</span>
                  <p>Pas de PRs récents</p>
                  <p className="text-xs mt-1">Continuez à rouler pour battre vos records!</p>
                </div>
              )}
            </div>
          )}

          {/* Starred Segments Tab */}
          {activeTab === "starred" && (
            <div className="space-y-3">
              {isLoadingStarred ? (
                <div className="flex justify-center py-8">
                  <div className="size-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
              ) : starredSegments.length > 0 ? (
                starredSegments.map((segment) => (
                  <StarredSegmentCard
                    key={segment.id}
                    segment={segment}
                    onClick={() => {
                      onSelectSegment?.(segment.id);
                      onClose();
                    }}
                  />
                ))
              ) : (
                <div className="text-center py-8 text-subtle-green">
                  <span className="material-symbols-outlined text-4xl mb-2">star</span>
                  <p>Pas de segments favoris</p>
                  <p className="text-xs mt-1">Ajoutez des segments à vos favoris sur Strava</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border">
          <a
            href={`https://www.strava.com/athletes/${athlete?.id}`}
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
