"use client";

/**
 * Compact, Claude-Code-style Strava API usage bar for the app header.
 *
 * Shows the short-term (15-min) usage against Strava's limit ("API Strava
 * 42/100") with a colored fill (green < 70%, amber 70-90%, red > 90%). When
 * usage is high OR a 429 just occurred, it also shows a "réinitialisation dans
 * m:ss" cooldown countdown.
 *
 * The cooldown is derived from the current wall-clock time: Strava's 15-min
 * window is wall-clock aligned, so seconds-until-reset == 900 - (epoch % 900),
 * identical to the backend's seconds_until_reset but always fresh (no drift
 * between polls). A local 1-second tick advances it; crossing a window boundary
 * refetches the usage so the new window's near-zero count surfaces promptly.
 *
 * Renders nothing until the backend has captured at least one usage snapshot
 * (status/updated_at null), so it stays out of the way when there's no data.
 */

import { useEffect, useRef, useState } from "react";
import { useRateLimit } from "@/hooks";

// Length of Strava's short-term window, in seconds (100 req / 15 min).
const WINDOW_SECONDS = 900;
// Usage ratio at/above which we consider the user "at risk" and surface the
// cooldown countdown.
const HIGH_USAGE_RATIO = 0.7;

/** Current wall-clock time in whole epoch seconds. */
function nowSeconds(): number {
  return Math.floor(Date.now() / 1000);
}

/** Format a whole number of seconds as "m:ss". */
function formatCountdown(totalSeconds: number): string {
  const safe = Math.max(0, totalSeconds);
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function RateLimitBar() {
  const { status, refresh } = useRateLimit();

  // A locally-ticking clock drives the countdown between polls.
  const [now, setNow] = useState(nowSeconds);
  useEffect(() => {
    const id = setInterval(() => setNow(nowSeconds()), 1000);
    return () => clearInterval(id);
  }, []);

  // Epoch of the last 429 (dispatched app-wide by fetchAPI). Kept as a timestamp
  // rather than a boolean so "recent" naturally expires when the window rolls
  // over — no effect-based clearing needed.
  const [lastRateLimitAt, setLastRateLimitAt] = useState<number | null>(null);
  useEffect(() => {
    if (typeof window === "undefined") return;
    const handler = () => setLastRateLimitAt(nowSeconds());
    window.addEventListener("kom:ratelimit", handler);
    return () => window.removeEventListener("kom:ratelimit", handler);
  }, []);

  const windowIndex = Math.floor(now / WINDOW_SECONDS);

  // When the 15-min window rolls over, refetch fresh usage (refresh() only
  // setState's asynchronously, so this stays out of the render path).
  const prevWindowRef = useRef(windowIndex);
  useEffect(() => {
    if (prevWindowRef.current !== windowIndex) {
      prevWindowRef.current = windowIndex;
      refresh();
    }
  }, [windowIndex, refresh]);

  // No snapshot yet — stay invisible.
  if (!status || status.updated_at === null) return null;

  const { usage, limit } = status.short_term;
  if (usage === null || limit === null || limit <= 0) return null;

  const ratio = Math.min(1, Math.max(0, usage / limit));
  const pctWidth = `${(ratio * 100).toFixed(0)}%`;

  // green < 70% | amber 70-90% | red > 90%
  const fillClass =
    ratio > 0.9
      ? "bg-red-500"
      : ratio >= HIGH_USAGE_RATIO
        ? "bg-amber-500"
        : "bg-green-500";

  const recent429 =
    lastRateLimitAt !== null &&
    Math.floor(lastRateLimitAt / WINDOW_SECONDS) === windowIndex;
  const secondsLeft = WINDOW_SECONDS - (now % WINDOW_SECONDS);
  const showCooldown = recent429 || ratio >= HIGH_USAGE_RATIO;

  return (
    <div
      className="hidden sm:flex flex-col justify-center gap-1 min-w-[120px] max-w-[160px]"
      title={`Utilisation de l'API Strava : ${usage}/${limit} sur 15 min`}
      aria-label={`Utilisation API Strava ${usage} sur ${limit}`}
    >
      <div className="flex items-center justify-between gap-2 text-[10px] font-medium leading-none text-subtle-green">
        <span>API Strava</span>
        <span className="tabular-nums text-foreground">
          {usage}/{limit}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
        <div
          className={`h-full rounded-full transition-all duration-500 ${fillClass}`}
          style={{ width: pctWidth }}
        />
      </div>
      {showCooldown && (
        <span className="text-[10px] leading-none text-subtle-green tabular-nums">
          réinitialisation dans {formatCountdown(secondsLeft)}
        </span>
      )}
    </div>
  );
}
