# CLAUDE.md — KOMHunter agent guide

Single source of truth for AI agents working in this repo. If another doc contradicts this file, this file wins (and should be updated).

KOMHunter finds "huntable" Strava segments around a location: Strava OAuth login, segment search + difficulty scoring, Leaflet map + results table + segment detail panel, deep links to `strava.com/segments/{id}`.

## Architecture map

```
backend/                      FastAPI (Python 3.11+), port 8000
├── app/
│   ├── main.py               App factory, CORS (must expose X-KOM-Refreshed-Token)
│   ├── config.py             Pydantic Settings (reads backend/.env)
│   ├── api/
│   │   ├── dependencies.py   Auth dependencies: JWT verify + transparent Strava refresh
│   │   └── routes/
│   │       ├── auth.py       /api/auth: login, callback, refresh, me
│   │       ├── segments.py   /api/segments: explore (+ climb-cat/grade/distance filters), geocode, {id}
│   │       ├── athletes.py   /api/athletes: me, me/stats, me/koms, me/starred, me/prs, me/heatmap
│   │       └── health.py     /api/health (+ /ready, /live)
│   ├── services/
│   │   ├── strava_auth.py    OAuth URLs, token exchange/refresh, JWT mint/verify
│   │   ├── strava_api.py     Async httpx client for the Strava REST API
│   │   ├── geocoding.py      Nominatim geocoding (in-memory cache, Paris fallback)
│   │   └── scoring.py        Terrain-first, sport-aware difficulty (0-100); prestige + competitiveness kept SEPARATE
│   ├── models/               Pydantic v2 schemas: auth.py, segment.py, athlete.py
│   └── utils/                formatters.py, polyline.py
└── tests/                    pytest (+ respx for Strava mocks), conftest.py sets env vars

frontend/                     Next.js 16 + TypeScript + Tailwind, Bun, port 3000
└── src/
    ├── app/                  App router: layout.tsx (shared StravaProvider), page.tsx (/ hunt),
    │                         search/page.tsx (/search advanced filters), settings/page.tsx (/settings)
    ├── components/           layout/ (Header w/ Explorer/Recherche nav + settings), hunt/ (simple
    │                         form + AdvancedSearchForm), map/ (SegmentMap: Leaflet + leaflet.heat
    │                         heatmap), segments/ (table + detail panel), dashboard/ (stats, KOMs —
    │                         cards click through to segment detail), ui/
    ├── hooks/                useStrava (auth state), useSegments, useAthleteStats, useHeatmap, useSettings
    ├── lib/                  api.ts (typed API client, ApiError), utils.ts
    └── types/                Shared TypeScript interfaces
```

## Commands

Bun is NOT on PATH in agent shells — invoke it as `$HOME/.bun/bin/bun` (the Makefile handles this itself).

```bash
make start-backend      # backend on :8000 (background, logs in .backend.log)
make start-frontend     # frontend on :3000 (background, logs in .frontend.log)
make stop               # stop both
make reboot             # stop + restart both
make install            # backend venv + pip install, frontend bun install

# Backend tests
cd backend && ./venv/bin/pytest

# Frontend checks
cd frontend && bun run lint
cd frontend && bun test
cd frontend && bun run build

# Smoke test (services must be running)
bash scripts/smoke.sh
```

## Conventions

- **Bun, NEVER npm/npx/yarn** for anything in `frontend/` (lockfile is `bun.lock`).
- **Theme is Strava-orange, light** (`--primary #fc4c02`, `<html className="light">` in `layout.tsx`). The old green is gone — don't reintroduce it. Bike/run differentiation uses sport accents `--sport-ride` (orange) / `--sport-run` (blue); segments carry `activity_type` and the scoring is sport-aware.
- TypeScript strict mode; interfaces for all API responses in `src/types/`.
- Pydantic v2 models for every backend request/response schema.
- Async everywhere on the backend; external HTTP via async `httpx`.
- Conventional commits (`feat:`, `fix:`, `docs:`, ...).
- Never commit secrets; `backend/.env` is real credentials — do not read or print it.

## Auth contract (the part that broke once — keep it intact)

- The backend's OAuth callback mints a **JWT that wraps the Strava tokens** (`access_token`, `refresh_token`, `expires_at`, `sub` = athlete id) and redirects to the frontend with the JWT in the **URL fragment** (`/#token=<JWT>`), never a query param.
- The frontend stores it as `kom_token` and sends `Authorization: Bearer <JWT>` on every API call.
- Protected endpoints **decode and verify the JWT** (`dependencies.py`), then call Strava with the *inner* `access_token`. The JWT itself is never forwarded to Strava.
- If the inner Strava token is expired, the dependency refreshes it against Strava, mints a new JWT, and sets it on the response header **`X-KOM-Refreshed-Token`**. The frontend's `fetchAPI` checks this header on every response and re-stores `kom_token`. CORS must keep `expose_headers=["X-KOM-Refreshed-Token"]` or the browser cannot read it.
- `POST /api/auth/refresh` is **JWT-in / JWT-out** (`{"token": "<jwt>"}` → `{"token": "<new jwt>"}`): signature always verified, expiry not enforced on input. Raw Strava tokens never reach the browser.
- `GET /api/auth/me` returns session metadata (athlete id, expiries) from the JWT; if the inner Strava token is stale it is transparently refreshed first (one Strava call + `X-KOM-Refreshed-Token`).
- Invalid/forged/expired-session JWT → 401 "Invalid or expired session - please log in with Strava again" (ASCII hyphen — the frontend matches on `ApiError.status`, not the string, but keep the detail text stable). The frontend only clears the stored token on a 401 (`ApiError.status === 401`), never on network errors; a Strava outage surfaces as 503 "Strava is unreachable - try again later".

## Gotchas

- **Strava rate limits**: 100 requests / 15 min and 1000 / day per app. Segment exploration does 1 explore + N detail calls, so keep result counts small when testing.
- **Two expiry clocks**: Strava access tokens live ~6 hours; the JWT session lives 7 days. The auto-refresh above bridges the gap — do not "simplify" it away.
- **OAuth `state` is stored in an in-memory dict** in the backend → run a **single worker** (the default `uvicorn` dev command is fine; multiple workers break the OAuth flow).
- **Segment leaderboards are premium-only** (Strava returns 403). KOM/QOM data comes from the `xoms` field of `GET /segments/{id}` instead — do not reintroduce leaderboard calls.
- **Difficulty is terrain-only.** `scoring.py` returns a sport-aware terrain difficulty (0-100); `prestige` (popularity) and `competitiveness` (KOM speed) are computed but exposed as **separate** fields on `DifficultyBreakdown`, never summed into difficulty. Do not re-blend them — that reintroduces the "short popular ramp scores hard" bug.
- **Training heatmap** (`GET /api/athletes/me/heatmap`) decodes activity `summary_polyline`s. It is deliberately bounded (≤5 Strava pages, down-sampled to ~5000 points) and backed by a per-athlete in-memory TTL cache (5 min, LRU-capped). Respect those caps; do not add unbounded pagination.
- Frontend tests use the **built-in Bun test runner** (with happy-dom preload via `bunfig.toml`), not vitest/jest.
- `conftest.py` sets required env vars before importing the app — backend tests need no `.env`.
- **Known limitation**: the session JWT is signed but not encrypted (JWS, not JWE) — anyone holding it can base64-decode the embedded Strava `access_token`/`refresh_token`. It lives in `localStorage`, so an XSS would expose the Strava tokens. Accepted trade-off for the current no-database design; the fix (server-side session store, e.g. Redis, with an opaque session id) is tracked in the GitHub issues.
