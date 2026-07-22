"use client";

/**
 * Sidebar component with hunt parameters
 */

import { HuntParameters } from "@/components/hunt/HuntParameters";
import { useStrava } from "@/hooks";
import type { HuntParameters as HuntParamsType } from "@/types";

interface SidebarProps {
  className?: string;
  onStartHunt: (params: HuntParamsType) => void;
  isLoading?: boolean;
  // Search center (shared with the map) — passed straight through to the form.
  location: string;
  latitude: number;
  longitude: number;
  onLocationChange: (location: string, lat: number, lon: number) => void;
}

export function Sidebar({
  className,
  onStartHunt,
  isLoading,
  location,
  latitude,
  longitude,
  onLocationChange,
}: SidebarProps) {
  const { logout, isAuthenticated } = useStrava();

  return (
    <aside
      className={`w-80 flex-shrink-0 border-r border-border bg-surface overflow-y-auto custom-scrollbar flex flex-col z-10 shadow-sm ${className}`}
    >
      <div className="p-6 space-y-8">
        {/* Headline */}
        <div>
          <h3 className="tracking-tight text-xl font-bold leading-tight">
            Hunt Parameters
          </h3>
          <p className="text-sm text-subtle-green mt-1">
            Configure your search area
          </p>
        </div>

        {/* Hunt Parameters Form */}
        <HuntParameters
          onSubmit={onStartHunt}
          isLoading={isLoading}
          location={location}
          latitude={latitude}
          longitude={longitude}
          onLocationChange={onLocationChange}
        />
      </div>

      {/* Sidebar Footer */}
      {isAuthenticated && (
        <div className="mt-auto p-6 border-t border-border">
          <button
            onClick={logout}
            className="flex w-full items-center justify-center gap-2 text-subtle-green hover:text-foreground text-sm font-medium transition-colors"
          >
            <span className="material-symbols-outlined text-lg">logout</span>
            Log Out
          </button>
        </div>
      )}
    </aside>
  );
}
