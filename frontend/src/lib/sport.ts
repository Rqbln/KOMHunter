/**
 * Sport-type helpers for bike/run differentiation.
 *
 * The backend tags segments with an `activity_type` of "riding" or "running".
 * These helpers derive the Material Symbols icon, a French label and the CSS
 * accent-color variable (blue for running, orange for riding) from it.
 */

function isRunning(activityType?: string): boolean {
  return (activityType ?? "").toLowerCase().startsWith("run");
}

/**
 * Material Symbols icon name for the given activity type.
 */
export function sportIcon(activityType?: string): string {
  return isRunning(activityType) ? "directions_run" : "directions_bike";
}

/**
 * Human-readable (French) label for the given activity type.
 */
export function sportLabel(activityType?: string): string {
  return isRunning(activityType) ? "Course" : "Vélo";
}

/**
 * CSS custom-property reference for the sport accent color.
 */
export function sportColorVar(activityType?: string): string {
  return isRunning(activityType) ? "var(--sport-run)" : "var(--sport-ride)";
}
