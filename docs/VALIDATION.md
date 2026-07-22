# KOMHunter - Validation Technique

Ce document résume les résultats de validation de la phase technique de KOMHunter.

## Phase 0: Validation des Outils

### MCP Chrome/Browser Extension
- **Status**: Validé
- **Test**: Navigation vers Strava.com + screenshot
- **Evidence**: `docs/poc-mcp-strava.png`

### BMAD
- **Status**: Documenté
- **Note**: Le framework BMAD est configuré via `.cursorrules` pour guider le développement

## Phase 1: Backend FastAPI

### Structure du Projet
- **Status**: Complète
- **Fichiers créés**: 25+ fichiers Python dans `backend/app/`

### Endpoints API

| Endpoint | Méthode | Status | Notes |
|----------|---------|--------|-------|
| `/api/health` | GET | Validé | Retourne status, version, timestamp |
| `/api/health/ready` | GET | Validé | Probe de readiness |
| `/api/health/live` | GET | Validé | Probe de liveness |
| `/api/auth/login` | GET | Validé | Redirection OAuth Strava |
| `/api/auth/callback` | GET | Implémenté | Callback OAuth |
| `/api/auth/refresh` | POST | Implémenté | Refresh token |
| `/api/segments/explore` | POST | Implémenté | Exploration segments |
| `/api/segments/{id}` | GET | Implémenté | Détails segment |
| `/api/segments/geocode` | GET | Implémenté | Géocodage |
| `/api/athletes/me` | GET | Implémenté | Profil utilisateur |

### Tests Unitaires
- **Total**: 58 tests
- **Passés**: 58/58 (100%)
- **Coverage**: ~68%

```
tests/test_auth.py          - 13 tests PASSED
tests/test_formatters.py    - 19 tests PASSED
tests/test_health.py        - 4 tests PASSED
tests/test_polyline.py      - 9 tests PASSED
tests/test_scoring.py       - 13 tests PASSED
```

## Phase 2: Intégration Strava API

### OAuth2 Flow
- **Status**: Implémenté
- **Fonctionnalités**:
  - Génération URL d'autorisation avec state CSRF
  - Échange code → tokens
  - Refresh de tokens expirés
  - Création de JWT session

### Endpoints Strava Supportés
- `GET /athlete` - Profil utilisateur
- `GET /segments/explore` - Exploration par bounding box
- `GET /segments/{id}` - Détails segment
- `GET /segments/{id}/leaderboard` - KOM/classement

## Phase 3: Services Métier

### Geocoding (Nominatim)
- **Status**: Implémenté
- **Features**:
  - Cache en mémoire
  - Fallback vers Paris
  - Reverse geocoding

### Scoring de Difficulté
- **Status**: Implémenté
- **Formule**: `(pente + 1) × speed_factor × distance_factor`
- **Catégories**: Easy, Moderate, Hard, Expert
- **Normalisation**: Échelle 0-100

### Polyline Decoding
- **Status**: Implémenté
- **Features**:
  - Décodage Google Polyline
  - Conversion vers GeoJSON
  - Fallback manuel si lib non disponible

## Phase 4: Frontend Next.js

### Configuration
- **Framework**: Next.js 16.1.6 (Turbopack)
- **Styling**: TailwindCSS avec thème KOMHunter
- **Font**: Lexend
- **Icons**: Material Symbols

### Composants Créés

| Composant | Status | Description |
|-----------|--------|-------------|
| Header | Complet | Navigation + user info |
| Sidebar | Complet | Hunt parameters |
| MainContent | Complet | Map + table container |
| HuntParameters | Complet | Formulaire de recherche |
| LocationInput | Complet | Input avec geocoding |
| SportTypeToggle | Complet | Run/Ride toggle |
| RadiusSlider | Complet | Slider avec labels |
| SegmentMap | Stub | Placeholder pour map |
| SegmentTable | Complet | Table des segments |
| SegmentRow | Complet | Ligne de segment |

### Theme Colors

```css
--primary: #0df259
--primary-hover: #0bc94a
--background-light: #f8fcf9
--background-dark: #102216
--surface-light: #ffffff
--surface-dark: #1a3322
--text-main: #0d1c12
--text-light: #ffffff
--border-light: #e7f4eb
--border-dark: #2a4533
--subtle-green: #499c65
```

### Build Status
- **Status**: Succès
- **Output**: Standalone (Docker-ready)

## Phase 5: Tests E2E

### Backend Health Check
```bash
curl http://localhost:8000/api/health
# {"status":"healthy","app_name":"KOMHunter API","version":"1.0.0",...}
```

### Frontend Rendering
- **Status**: Validé via MCP Browser
- **Evidence**: `docs/e2e-frontend.png`
- **Composants vérifiés**:
  - Header avec branding
  - Sidebar avec paramètres
  - Map placeholder
  - Table des segments

## Critères de Validation Finale

| Critère | Status |
|---------|--------|
| OAuth Strava implémenté | ✅ |
| Exploration segments | ✅ |
| Détails segment + KOM | ✅ |
| Geocoding avec cache | ✅ |
| Scoring calcule correctement | ✅ |
| Tests unitaires passent | ✅ |
| Frontend build réussi | ✅ |
| E2E validé avec MCP | ✅ |
| Documentation API (OpenAPI) | ✅ |

## Livrables

1. **Backend FastAPI** - `backend/`
   - API REST complète
   - Services métier
   - Tests unitaires

2. **Frontend Next.js** - `frontend/`
   - Structure de composants
   - Thème KOMHunter
   - Hooks de données

3. **Configuration**
   - Docker Compose
   - `.env.example` files
   - `.cursorrules`

4. **Documentation**
   - `docs/ARCHITECTURE.md`
   - `docs/VALIDATION.md`
   - OpenAPI à `/docs`

## Prochaines Étapes (Roadmap UX)

La phase technique est complète. La prochaine roadmap couvrira:

1. Intégration d'une vraie carte (Leaflet/Mapbox)
2. Design responsive mobile
3. Dark mode toggle
4. Animations et transitions
5. Gestion des erreurs UX
6. Notifications temps réel
7. Export de données (CSV/GPX)

---

## E2E browser checklist (v1 remediation) — 2026-07-22

Manual acceptance run in a real browser (http://localhost:3000, backend on :8000, valid Strava credentials in `backend/.env`). Check each step in order:

- [ ] **Login** — click "Login with Strava", authorize on strava.com, land back on the app authenticated (athlete name/avatar visible in the header).
- [ ] **Hunt** — enter location "Paris", radius 10 km, sport "riding", click "Start Hunt": the results table fills AND markers/polylines appear on the map.
- [ ] **Detail panel** — click a table row: the segment detail panel opens with the difficulty score breakdown (distance, elevation, grade, KOM/QOM time).
- [ ] **Strava deep link** — click "Voir sur Strava": a new tab opens on `strava.com/segments/{id}` for that segment.
- [ ] **Dashboard** — open the dashboard: athlete stats, KOMs, PRs, and starred segments load without errors.
- [ ] **Logout** — log out: the UI returns to the unauthenticated state.
- [ ] **Logged-out hunt** — while logged out, click "Start Hunt": the app shows the login CTA ("Log in with Strava to start hunting"), and NEVER a raw `Authorization header required` error (the original v1 bug).

---

## Wave 2 features checklist — 2026-07-22

Manual acceptance for the feature wave (terrain-first scoring, `/search`, `/settings`, heatmap, bike/run differentiation). Run in a real browser, authenticated. Check each in order:

- [ ] **Difficulty is terrain-first** — hunt an area with a short, popular urban ramp: its **difficulty** score reads easy/moderate (NOT "hard"), while its prestige/competitiveness may be high. Difficulty reflects terrain only, not popularity or KOM speed.
- [ ] **Sport-aware scoring** — the same location scored for "riding" vs "running" produces different difficulty values (climb-oriented vs grade-adjusted effort).
- [ ] **Advanced search (`/search`)** — set climb-category, average-grade, and distance filters; submit: the results table respects the filters and is sortable.
- [ ] **Clickable profile cards** — open the dashboard; click a KOM, PR, or starred card: the segment detail panel opens for that segment.
- [ ] **Map-click recenter** — click a point on the map: the search recenters there; the "Ma position" button recenters on the browser geolocation.
- [ ] **Training heatmap** — enable the heatmap overlay: your activity tracks render on the map; toggling the sport filter (ride/run) changes the points shown.
- [ ] **Bike/run differentiation** — segments show sport icons and accents (orange for riding, blue for running).
- [ ] **Settings persist (`/settings`)** — change default sport/radius and notification toggles, reload the page: the values are restored from localStorage.
