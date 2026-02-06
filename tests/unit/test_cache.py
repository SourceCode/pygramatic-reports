"""Tests for CacheManager."""

from pygramattic_reports.core.cache import CacheManager


def test_cache_put_get():
    cache = CacheManager(capacity=2)
    cache.put("k1", "v1")
    assert cache.get("k1") == "v1"
    assert cache.get("k2") is None


def test_lru_eviction():
    cache = CacheManager(capacity=2)
    cache.put("k1", "v1")
    cache.put("k2", "v2")
    cache.put("k3", "v3")  # Should evict k1

    assert cache.get("k1") is None
    assert cache.get("k2") == "v2"
    assert cache.get("k3") == "v3"


def test_lru_update():
    cache = CacheManager(capacity=2)
    cache.put("k1", "v1")
    cache.put("k2", "v2")
    cache.get("k1")  # Access k1, making k2 LRU
    cache.put("k3", "v3")  # Should evict k2

    assert cache.get("k1") == "v1"
    assert cache.get("k2") is None
    assert cache.get("k3") == "v3"


def test_memoize_decorator():
    cache = CacheManager()
    call_count = 0

    @cache.memoize()
    def expensive_func(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    assert expensive_func(5) == 10
    assert call_count == 1

    assert expensive_func(5) == 10
    assert call_count == 1  # Should be cached

    assert expensive_func(6) == 12
    assert call_count == 2
