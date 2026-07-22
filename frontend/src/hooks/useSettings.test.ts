import { describe, it, expect, beforeEach } from "bun:test";
import { getSettings, DEFAULT_SETTINGS } from "./useSettings";

const STORAGE_KEY = "kom_settings";

beforeEach(() => {
  localStorage.clear();
});

describe("getSettings", () => {
  it("returns the defaults when nothing is stored", () => {
    expect(getSettings()).toEqual(DEFAULT_SETTINGS);
  });

  it("merges a partial stored payload over the defaults", () => {
    // Older/partial payload: only some keys present.
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ defaultSport: "running", notifyWeeklySummary: true })
    );

    const settings = getSettings();
    expect(settings.defaultSport).toBe("running");
    expect(settings.notifyWeeklySummary).toBe(true);
    // Missing keys fall back to defaults.
    expect(settings.defaultRadiusKm).toBe(DEFAULT_SETTINGS.defaultRadiusKm);
    expect(settings.units).toBe(DEFAULT_SETTINGS.units);
  });

  it("falls back to the defaults on corrupt JSON", () => {
    localStorage.setItem(STORAGE_KEY, "{not valid json");
    expect(getSettings()).toEqual(DEFAULT_SETTINGS);
  });

  it("round-trips a full settings object written to localStorage", () => {
    const stored = {
      defaultSport: "running" as const,
      defaultRadiusKm: 42,
      units: "imperial" as const,
      notifyKomOpportunities: false,
      notifyWeeklySummary: true,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    expect(getSettings()).toEqual(stored);
  });
});
