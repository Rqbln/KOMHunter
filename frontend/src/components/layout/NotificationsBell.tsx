"use client";

/**
 * Notifications bell with a small anchored popover.
 *
 * There is no server-side push yet, so this surfaces the *local* notification
 * preferences (useSettings, localStorage-backed) as read-only status lines and
 * links to /settings to change them. The unread dot reflects real state: it
 * shows only when at least one notification preference is currently enabled.
 */

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSettings } from "@/hooks/useSettings";

function StatusLine({ label, enabled }: { label: string; enabled: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5">
      <span className="text-sm text-foreground">{label}</span>
      <span
        className={`inline-flex items-center gap-1 text-xs font-semibold ${
          enabled ? "text-primary" : "text-subtle-green"
        }`}
      >
        <span className="material-symbols-outlined text-sm leading-none">
          {enabled ? "check_circle" : "cancel"}
        </span>
        {enabled ? "activées" : "désactivées"}
      </span>
    </div>
  );
}

export function NotificationsBell() {
  const { settings } = useSettings();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const hasEnabled =
    settings.notifyKomOpportunities || settings.notifyWeeklySummary;

  // Close on outside pointer-down and on Escape.
  useEffect(() => {
    if (!open) return;
    function handlePointerDown(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-label="Notifications"
        aria-haspopup="dialog"
        aria-expanded={open}
        className="flex items-center justify-center rounded-full size-10 bg-border hover:bg-primary/20 transition-colors relative"
      >
        <span className="material-symbols-outlined text-[20px]">
          notifications
        </span>
        {hasEnabled && (
          <span
            aria-hidden="true"
            className="absolute top-2 right-2 size-2 bg-primary rounded-full"
          />
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Notifications"
          className="absolute right-0 top-full mt-2 w-72 rounded-xl border border-border bg-surface shadow-lg z-30 overflow-hidden"
        >
          <div className="flex items-center gap-2 border-b border-border px-4 py-3">
            <span className="material-symbols-outlined text-primary text-lg">
              notifications
            </span>
            <h3 className="text-sm font-bold">Notifications</h3>
          </div>

          <div className="px-4 py-2">
            <StatusLine
              label="Opportunités de KOM"
              enabled={settings.notifyKomOpportunities}
            />
            <StatusLine
              label="Résumé hebdomadaire"
              enabled={settings.notifyWeeklySummary}
            />
          </div>

          <p className="px-4 pb-2 text-xs text-subtle-green">
            Préférences locales uniquement — aucune notification n&apos;est
            encore envoyée par le serveur.
          </p>

          <Link
            href="/settings"
            onClick={() => setOpen(false)}
            className="flex items-center justify-between gap-2 border-t border-border px-4 py-3 text-sm font-medium text-primary hover:bg-primary/10 transition-colors"
          >
            Gérer dans les réglages
            <span className="material-symbols-outlined text-lg">
              chevron_right
            </span>
          </Link>
        </div>
      )}
    </div>
  );
}
