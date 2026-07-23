"""
Small in-memory TTL cache with LRU-bounded capacity.

Mirrors the pattern already used by the training-heatmap cache (routes/athletes)
and enrichment's segment-detail cache: an ``OrderedDict``-backed store where every
write sweeps expired entries and evicts least-recently-used entries beyond a hard
cap, so worst-case memory stays bounded no matter how many distinct (often
user-controlled) keys are seen. Reads refresh recency and lazily drop the key if
it has expired.

Single-process, not thread-safe by design — it is only touched from within the
event loop's request handling, which is cooperatively scheduled.
"""
import time
from collections import OrderedDict
from typing import Any, Hashable, Optional, Tuple


class TTLCache:
    """A single-process TTL cache bounded by LRU eviction."""

    def __init__(self, ttl: float, max_entries: int = 256) -> None:
        """
        Args:
            ttl: Entry lifetime in seconds (uses a monotonic clock).
            max_entries: Hard cap on stored entries; oldest are evicted first.
        """
        self.ttl = ttl
        self.max_entries = max_entries
        self._store: "OrderedDict[Hashable, Tuple[float, Any]]" = OrderedDict()

    def get(self, key: Hashable) -> Optional[Any]:
        """Return the cached value for ``key`` if present and not expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if time.monotonic() - stored_at > self.ttl:
            self._store.pop(key, None)
            return None
        # Mark most-recently-used so it survives LRU eviction longest.
        self._store.move_to_end(key)
        return value

    def set(self, key: Hashable, value: Any) -> None:
        """Store ``value`` under ``key``, keeping the cache bounded.

        Every write (1) sweeps all expired entries so stale keys can't
        accumulate even when they're never re-read, and (2) evicts the
        least-recently-used entries until the count is within ``max_entries``.
        """
        now = time.monotonic()

        # Sweep expired entries (list() snapshots keys so we can mutate safely).
        for cached_key, (stored_at, _) in list(self._store.items()):
            if now - stored_at > self.ttl:
                self._store.pop(cached_key, None)

        self._store[key] = (now, value)
        self._store.move_to_end(key)

        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)

    def clear(self) -> None:
        """Drop all entries (used for test isolation)."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: Hashable) -> bool:
        return self.get(key) is not None
