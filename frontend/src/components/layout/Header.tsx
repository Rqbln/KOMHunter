"use client";

/**
 * Header component with navigation and user info
 */

import { useStrava } from "@/hooks";

interface HeaderProps {
  className?: string;
  onOpenDashboard?: () => void;
}

export function Header({ className, onOpenDashboard }: HeaderProps) {
  const { athlete, isAuthenticated, login, logout } = useStrava();

  return (
    <header
      className={`flex items-center justify-between whitespace-nowrap border-b border-border px-6 py-3 bg-surface z-20 ${className}`}
    >
      {/* Logo */}
      <div className="flex items-center gap-4">
        <div className="size-8 flex items-center justify-center text-primary">
          <span className="material-symbols-outlined text-3xl">bolt</span>
        </div>
        <h2 className="text-xl font-bold leading-tight tracking-[-0.015em]">
          KOMHunter
        </h2>
      </div>

      {/* Right side */}
      <div className="flex flex-1 justify-end gap-6 items-center">
        {/* Action buttons */}
        <div className="hidden md:flex gap-2">
          <button className="flex items-center justify-center rounded-full size-10 bg-border hover:bg-primary/20 transition-colors">
            <span className="material-symbols-outlined text-[20px]">settings</span>
          </button>
          <button className="flex items-center justify-center rounded-full size-10 bg-border hover:bg-primary/20 transition-colors relative">
            <span className="material-symbols-outlined text-[20px]">
              notifications
            </span>
            <span className="absolute top-2 right-2 size-2 bg-primary rounded-full"></span>
          </button>
        </div>

        {/* User info */}
        {isAuthenticated && athlete ? (
          <button 
            onClick={onOpenDashboard}
            className="flex items-center gap-3 pl-4 border-l border-border hover:opacity-80 transition-opacity"
          >
            <div
              className="bg-center bg-no-repeat bg-cover rounded-full size-10 border-2 border-primary"
              style={{
                backgroundImage: athlete.profile
                  ? `url("${athlete.profile}")`
                  : undefined,
              }}
            />
            <div className="hidden lg:block text-left">
              <p className="text-sm font-bold leading-tight">
                {athlete.firstname} {athlete.lastname}
              </p>
              <p className="text-xs text-subtle-green">
                {athlete.premium ? "Pro Member" : "Member"}
              </p>
            </div>
            <span className="material-symbols-outlined text-subtle-green">chevron_right</span>
          </button>
        ) : (
          <button
            onClick={login}
            className="px-4 py-2 bg-primary text-black rounded-full font-bold text-sm hover:bg-primary-hover transition-colors"
          >
            Log In with Strava
          </button>
        )}
      </div>
    </header>
  );
}
