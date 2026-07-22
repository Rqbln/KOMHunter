"use client";

/**
 * KOMHunter — Settings (/settings)
 *
 * Client-only user preferences backed by localStorage (see useSettings). Two
 * groups:
 *   - Préférences: default hunt sport + radius (seed the hunt form on "/"),
 *     and a display-unit preference.
 *   - Notifications: local opt-ins with no server delivery yet.
 *
 * Auth-gated like /search: unauthenticated visitors get a Strava login CTA.
 */

import { Header } from "@/components/layout/Header";
import { SportTypeToggle } from "@/components/hunt/SportTypeToggle";
import { RadiusSlider } from "@/components/hunt/RadiusSlider";
import { useStrava, useSettings } from "@/hooks";
import type { SettingsUnits } from "@/hooks";

/** Segmented métrique / impérial control (styled like SportTypeToggle). */
function UnitsToggle({
  value,
  onChange,
}: {
  value: SettingsUnits;
  onChange: (value: SettingsUnits) => void;
}) {
  const options: { value: SettingsUnits; label: string }[] = [
    { value: "metric", label: "Métrique (km)" },
    { value: "imperial", label: "Impérial (mi)" },
  ];
  return (
    <div className="flex h-12 w-full items-center justify-center rounded-full border border-border bg-background p-1">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          aria-pressed={value === option.value}
          className={`flex h-full grow items-center justify-center rounded-full px-2 text-sm font-bold leading-normal transition-all duration-200 ${
            value === option.value
              ? "bg-primary text-black shadow-sm"
              : "text-subtle-green"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

/** Accessible on/off switch in the Strava-orange theme. */
function ToggleSwitch({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors ${
        checked ? "bg-primary" : "bg-border"
      }`}
    >
      <span
        className={`inline-block size-4 transform rounded-full bg-white shadow transition-transform ${
          checked ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

/** A labelled notification row with a trailing switch. */
function NotificationRow({
  title,
  description,
  checked,
  onChange,
}: {
  title: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <div className="min-w-0">
        <p className="text-sm font-semibold">{title}</p>
        <p className="mt-0.5 text-sm text-subtle-green">{description}</p>
      </div>
      <ToggleSwitch checked={checked} onChange={onChange} label={title} />
    </div>
  );
}

function SettingsPageContent() {
  const { isAuthenticated, isLoading: isAuthLoading, login } = useStrava();
  const { settings, update } = useSettings();

  // useStrava starts in a loading state and only resolves after mount, so this
  // spinner naturally covers the brief window in which useSettings is still
  // serving defaults before the persisted values hydrate — no separate gate.
  const showSpinner = isAuthLoading;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1 overflow-y-auto custom-scrollbar">
        {showSpinner ? (
          <div className="flex items-center justify-center py-32">
            <span className="material-symbols-outlined text-4xl text-subtle-green animate-spin">
              progress_activity
            </span>
          </div>
        ) : !isAuthenticated ? (
          <div className="flex items-center justify-center px-4 py-24">
            <div className="max-w-md w-full text-center rounded-2xl border border-border bg-surface p-8 shadow-sm">
              <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full bg-primary/15 text-primary">
                <span className="material-symbols-outlined text-3xl">
                  settings
                </span>
              </div>
              <h1 className="text-xl font-bold">Réglages</h1>
              <p className="mt-2 text-sm text-subtle-green">
                Connectez-vous avec Strava pour personnaliser vos préférences de
                chasse et vos notifications.
              </p>
              <button
                onClick={login}
                className="mt-6 inline-flex items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-bold text-black transition-colors hover:bg-primary-hover"
              >
                <span className="material-symbols-outlined text-lg">bolt</span>
                Se connecter avec Strava
              </button>
            </div>
          </div>
        ) : (
          <div className="mx-auto w-full max-w-2xl px-4 py-8 lg:px-6">
            {/* Page heading */}
            <div className="mb-8">
              <h1 className="text-2xl font-bold tracking-tight">Réglages</h1>
              <p className="mt-1 text-sm text-subtle-green">
                Vos préférences sont enregistrées localement sur cet appareil.
              </p>
            </div>

            <div className="space-y-6">
              {/* Préférences */}
              <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
                <div className="mb-5 flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">
                    tune
                  </span>
                  <h2 className="text-lg font-bold">Préférences</h2>
                </div>

                <div className="space-y-6">
                  {/* Default sport */}
                  <div>
                    <p className="mb-3 text-sm font-medium">Sport par défaut</p>
                    <SportTypeToggle
                      value={settings.defaultSport}
                      onChange={(value) => update({ defaultSport: value })}
                    />
                    <p className="mt-2 text-xs text-subtle-green">
                      Sélection initiale du formulaire de chasse (Vélo / Course).
                    </p>
                  </div>

                  {/* Default radius */}
                  <div>
                    <RadiusSlider
                      label="Rayon de recherche par défaut"
                      value={settings.defaultRadiusKm}
                      min={1}
                      max={100}
                      unit="km"
                      onChange={(value) => update({ defaultRadiusKm: value })}
                    />
                  </div>

                  {/* Units */}
                  <div>
                    <p className="mb-3 text-sm font-medium">Unités</p>
                    <UnitsToggle
                      value={settings.units}
                      onChange={(value) => update({ units: value })}
                    />
                    <p className="mt-2 text-xs text-subtle-green">
                      Préférence d&apos;affichage — enregistrée mais pas encore
                      appliquée : les distances restent en kilomètres pour le
                      moment.
                    </p>
                  </div>
                </div>
              </section>

              {/* Notifications */}
              <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
                <div className="mb-2 flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary">
                    notifications
                  </span>
                  <h2 className="text-lg font-bold">Notifications</h2>
                </div>
                <p className="mb-2 text-sm text-subtle-green">
                  Préférences locales uniquement — aucune notification n&apos;est
                  encore envoyée par le serveur.
                </p>

                <div className="divide-y divide-border">
                  <NotificationRow
                    title="Opportunités de KOM"
                    description="M'alerter des segments proches où un KOM/QOM semble accessible."
                    checked={settings.notifyKomOpportunities}
                    onChange={(value) =>
                      update({ notifyKomOpportunities: value })
                    }
                  />
                  <NotificationRow
                    title="Résumé hebdomadaire"
                    description="Recevoir un récapitulatif hebdomadaire de mes chasses et efforts."
                    checked={settings.notifyWeeklySummary}
                    onChange={(value) => update({ notifyWeeklySummary: value })}
                  />
                </div>
              </section>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function SettingsPage() {
  return <SettingsPageContent />;
}
