"use client";

/**
 * Header component with navigation and user info
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useStrava } from "@/hooks";
import { NotificationsBell } from "./NotificationsBell";

interface HeaderProps {
  className?: string;
  onOpenDashboard?: () => void;
}

const NAV_LINKS: { href: string; label: string }[] = [
  { href: "/", label: "Explorer" },
];

export function Header({ className, onOpenDashboard }: HeaderProps) {
  const { athlete, isAuthenticated, login } = useStrava();
  const pathname = usePathname();

  return (
    <header
      className={`flex items-center justify-between whitespace-nowrap border-b border-border px-6 py-3 bg-surface z-20 ${className}`}
    >
      {/* Logo + navigation */}
      <div className="flex items-center gap-4">
        <div className="size-8 flex items-center justify-center text-primary">
          <span className="material-symbols-outlined text-3xl">bolt</span>
        </div>
        <h2 className="text-xl font-bold leading-tight tracking-[-0.015em]">
          KOMHunter
        </h2>

        {/* Primary navigation */}
        <nav className="hidden md:flex items-center gap-1 ml-4">
          {NAV_LINKS.map(({ href, label }) => {
            const isActive = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={isActive ? "page" : undefined}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-subtle-green hover:text-foreground hover:bg-border"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Right side */}
      <div className="flex flex-1 justify-end gap-6 items-center">
        {/* Action buttons */}
        <div className="hidden md:flex gap-2">
          <Link
            href="/settings"
            aria-label="Réglages"
            aria-current={pathname === "/settings" ? "page" : undefined}
            className={`flex items-center justify-center rounded-full size-10 transition-colors ${
              pathname === "/settings"
                ? "bg-primary/20 text-primary"
                : "bg-border hover:bg-primary/20"
            }`}
          >
            <span className="material-symbols-outlined text-[20px]">settings</span>
          </Link>
          <NotificationsBell />
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
