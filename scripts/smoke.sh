#!/usr/bin/env bash
#
# KOMHunter smoke tests — curl assertions against a locally running stack.
#
# REQUIRES: the full stack must be up first — run `make reboot` before this
# script (backend on :8000, frontend on :3000).
#
# Exits non-zero if any check fails. Prints PASS/FAIL per check and a
# final summary line "SMOKE: X/Y passed".

set -euo pipefail

BACKEND="http://localhost:8000"
FRONTEND="http://localhost:3000"

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "PASS: $1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "FAIL: $1"
}

# --- Check 1: health endpoint returns 200 -----------------------------------
check_health() {
  local name="GET /api/health -> 200"
  local status
  status=$(curl -s -o /dev/null -w '%{http_code}' "$BACKEND/api/health" || echo "000")
  if [ "$status" = "200" ]; then
    pass "$name"
  else
    fail "$name (got HTTP $status)"
  fi
}

# --- Check 2: explore without auth -> 401 with clear JSON error -------------
check_explore_no_auth() {
  local name="POST /api/segments/explore (no auth) -> 401 + 'Authorization header required'"
  local body status
  body=$(curl -s -w '\n%{http_code}' -X POST "$BACKEND/api/segments/explore" \
    -H "Content-Type: application/json" \
    -d '{"location": "Paris", "radius_km": 10, "activity_type": "riding"}' || echo -e "\n000")
  status=$(echo "$body" | tail -n1)
  body=$(echo "$body" | sed '$d')
  if [ "$status" = "401" ] && echo "$body" | grep -q "Authorization header required"; then
    pass "$name"
  else
    fail "$name (got HTTP $status, body: $body)"
  fi
}

# --- Check 3: explore with bogus JWT -> 401 (JWT verification is active) ----
check_explore_bogus_jwt() {
  local name="POST /api/segments/explore (bogus JWT) -> 401 (JWT verification active)"
  local status
  status=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BACKEND/api/segments/explore" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer bogus.jwt.token" \
    -d '{"location": "Paris", "radius_km": 10, "activity_type": "riding"}' || echo "000")
  if [ "$status" = "401" ]; then
    pass "$name"
  else
    fail "$name (got HTTP $status — a non-401 means bogus tokens are not rejected: the original bug class)"
  fi
}

# --- Check 4: login redirects to strava.com ---------------------------------
check_login_redirect() {
  local name="GET /api/auth/login -> 302/307 with Location -> strava.com"
  local headers status location
  headers=$(curl -s -o /dev/null -D - "$BACKEND/api/auth/login" || echo "")
  status=$(echo "$headers" | head -n1 | awk '{print $2}')
  location=$(echo "$headers" | grep -i '^location:' | tr -d '\r' || true)
  if { [ "$status" = "302" ] || [ "$status" = "307" ]; } && echo "$location" | grep -qi "strava.com"; then
    pass "$name"
  else
    fail "$name (got HTTP ${status:-none}, ${location:-no Location header})"
  fi
}

# --- Check 5: frontend serves the app ---------------------------------------
check_frontend() {
  local name="GET :3000/ -> 200"
  local status
  status=$(curl -s -o /dev/null -w '%{http_code}' "$FRONTEND/" || echo "000")
  if [ "$status" = "200" ]; then
    pass "$name"
  else
    fail "$name (got HTTP $status)"
  fi
}

check_health
check_explore_no_auth
check_explore_bogus_jwt
check_login_redirect
check_frontend

TOTAL=$((PASS_COUNT + FAIL_COUNT))
echo ""
echo "SMOKE: $PASS_COUNT/$TOTAL passed"

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
