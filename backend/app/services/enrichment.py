"""
On-demand enrichment of segment summaries with popularity/competitiveness data.

Strava's ``/segments/explore`` returns only lightweight geometry
(id/name/distance/avg_grade/elev_difference/latlng) — it does NOT include
``effort_count``, ``athlete_count`` or the KOM time needed to score popularity
(prestige) and competitiveness. Those live only in ``GET /segments/{id}``.

This module fetches per-segment detail *only* when the caller needs an enriched
sort (popularity/competitiveness/opportunity), with three guardrails so a single
explore request can never hammer Strava or exhaust its rate budget:

- a hard cap on how many segments are enriched per request,
- bounded concurrency via an :class:`asyncio.Semaphore`, and
- a short-TTL, size-bounded in-memory cache of raw detail dicts keyed by
  segment id, so repeated sorts/searches over the same area don't re-fetch.

Enrichment is best-effort: a per-segment failure leaves that summary's
enrichment fields ``None`` (the caller sorts those last) rather than failing the
whole request.
"""
import asyncio
import logging
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from app.models.segment import SegmentSummary
from app.services.scoring import ScoringService
from app.services.strava_api import StravaAPIService
from app.utils.formatters import parse_time_to_seconds

logger = logging.getLogger(__name__)

# --- Enrichment tuning -----------------------------------------------------
# Never issue more than this many segment-detail calls for a single explore
# request, regardless of how many segments matched (protects Strava's rate
# limit: 100 req/15min, 1000/day). Explore itself returns ~10 segments, so this
# is a generous ceiling; anything beyond it is dropped (and logged).
_ENRICH_MAX_SEGMENTS = 40
# Bounded concurrency for the fan-out of detail calls.
_ENRICH_CONCURRENCY = 6

# Raw segment-detail cache. Keyed by segment id, short TTL so repeated sorts /
# searches over the same area reuse detail instead of re-hitting Strava.
# Backed by an OrderedDict with a hard size cap + expiry sweep on every write so
# it stays bounded no matter how many distinct segments are seen.
_DETAIL_CACHE_TTL = 600.0  # seconds
_DETAIL_CACHE_MAX_ENTRIES = 1024
_DETAIL_CACHE: "OrderedDict[int, Tuple[float, Dict[str, Any]]]" = OrderedDict()


def _detail_cache_get(segment_id: int) -> Optional[Dict[str, Any]]:
    """Return a cached raw detail dict for ``segment_id`` if present/fresh."""
    entry = _DETAIL_CACHE.get(segment_id)
    if entry is None:
        return None
    stored_at, value = entry
    if time.monotonic() - stored_at > _DETAIL_CACHE_TTL:
        _DETAIL_CACHE.pop(segment_id, None)
        return None
    _DETAIL_CACHE.move_to_end(segment_id)
    return value


def _detail_cache_set(segment_id: int, value: Dict[str, Any]) -> None:
    """Store ``value`` under ``segment_id``, keeping the cache bounded."""
    now = time.monotonic()

    # Sweep expired entries so stale keys can't accumulate even if never re-read.
    for cached_id, (stored_at, _) in list(_DETAIL_CACHE.items()):
        if now - stored_at > _DETAIL_CACHE_TTL:
            _DETAIL_CACHE.pop(cached_id, None)

    _DETAIL_CACHE[segment_id] = (now, value)
    _DETAIL_CACHE.move_to_end(segment_id)

    # Hard size cap via LRU eviction (oldest first).
    while len(_DETAIL_CACHE) > _DETAIL_CACHE_MAX_ENTRIES:
        _DETAIL_CACHE.popitem(last=False)


def _apply_enrichment(
    summary: SegmentSummary,
    detail: Dict[str, Any],
    scoring_service: ScoringService,
) -> None:
    """Populate a summary's enrichment fields from a raw detail dict (in place)."""
    effort_count = detail.get("effort_count")
    athlete_count = detail.get("athlete_count")

    xoms = detail.get("xoms") or {}
    kom_time_str = xoms.get("kom")
    kom_time_seconds = parse_time_to_seconds(kom_time_str)

    # Prefer detail's own distance/grade (authoritative); fall back to the
    # explore summary values when detail omits them.
    distance_m = detail.get("distance") or summary.distance
    avg_grade = detail.get("average_grade")
    if avg_grade is None:
        avg_grade = summary.avg_grade
    # Strava detail carries "Ride"/"Run"; scoring normalizes it internally.
    activity_type = detail.get("activity_type") or summary.activity_type or "riding"

    summary.prestige_score = scoring_service.compute_prestige_score(
        effort_count=effort_count,
        athlete_count=athlete_count,
    )
    summary.competitiveness_score = scoring_service.compute_competitiveness_score(
        distance_m=distance_m,
        kom_time_seconds=kom_time_seconds,
        avg_grade=avg_grade,
        activity_type=activity_type,
    )
    summary.effort_count = effort_count
    summary.athlete_count = athlete_count
    summary.kom_time = kom_time_str


async def enrich_segments(
    summaries: List[SegmentSummary],
    strava_service: StravaAPIService,
    scoring_service: ScoringService,
) -> List[SegmentSummary]:
    """
    Enrich ``summaries`` in place with prestige/competitiveness data.

    For each of the first ``_ENRICH_MAX_SEGMENTS`` summaries, fetch (or reuse a
    cached) segment detail — bounded by a concurrency semaphore — and compute
    prestige + competitiveness. Per-segment failures are swallowed: the affected
    summary keeps ``None`` enrichment fields so the caller can sort it last.

    Returns the same list object for convenience.
    """
    if not summaries:
        return summaries

    to_enrich = summaries[:_ENRICH_MAX_SEGMENTS]
    dropped = len(summaries) - len(to_enrich)
    if dropped > 0:
        logger.warning(
            "Enrichment cap reached: enriching %d of %d segments (%d left unenriched)",
            len(to_enrich),
            len(summaries),
            dropped,
        )

    semaphore = asyncio.Semaphore(_ENRICH_CONCURRENCY)

    async def _fetch_detail(summary: SegmentSummary) -> Dict[str, Any]:
        cached = _detail_cache_get(summary.id)
        if cached is not None:
            return cached
        async with semaphore:
            # Re-check the cache after acquiring the semaphore: a sibling task in
            # this same batch may have populated it while we were queued.
            cached = _detail_cache_get(summary.id)
            if cached is not None:
                return cached
            detail = await strava_service.get_segment_details(summary.id)
            _detail_cache_set(summary.id, detail)
            return detail

    results = await asyncio.gather(
        *(_fetch_detail(s) for s in to_enrich),
        return_exceptions=True,
    )

    for summary, result in zip(to_enrich, results):
        if isinstance(result, Exception):
            # Leave enrichment fields None; caller sorts this segment last.
            logger.warning(
                "Failed to enrich segment %s: %s", summary.id, result
            )
            continue
        _apply_enrichment(summary, result, scoring_service)

    return summaries
