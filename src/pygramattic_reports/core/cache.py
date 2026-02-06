"""Caching mechanism for Pygramattic Reports."""

import functools
import hashlib
import pickle
from collections import OrderedDict
from collections.abc import Callable
from typing import Any, TypeVar

from pygramattic_reports.logging import get_logger

logger = get_logger("core.cache")

T = TypeVar("T")


class CacheManager:
    """Simple LRU Cache Manager."""

    def __init__(self, capacity: int = 128) -> None:
        """Initialize the cache with a maximum capacity."""
        self.capacity = capacity
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Retrieve an item from the cache."""
        if key in self._cache:
            # Move to end to show it was recently used
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def put(self, key: str, value: Any) -> None:
        """Add an item to the cache."""
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self.capacity:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> dict[str, int]:
        """Return cache statistics."""
        return {"hits": self._hits, "misses": self._misses, "size": len(self._cache)}

    def generate_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate a stable cache key from arguments."""
        # Simple pickling for stability, though not perfect for all types
        try:
            key_data = pickle.dumps((args, sorted(kwargs.items())))
            return hashlib.sha256(key_data).hexdigest()
        except Exception:
            # If pickling fails, fallback to string representation (less reliable)
            logger.warning("Failed to pickle arguments for cache key generation")
            return hashlib.sha256(str((args, kwargs)).encode("utf-8")).hexdigest()

    def memoize(self) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator for memoizing function calls."""

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                # Include function name in key
                base_key = self.generate_key(*args, **kwargs)
                final_key = f"{func.__module__}.{func.__name__}:{base_key}"

                cached = self.get(final_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    from typing import cast

                    return cast("T", cached)

                result = func(*args, **kwargs)
                self.put(final_key, result)
                return result

            return wrapper

        return decorator


# Global instance
_GlobalCache = CacheManager()


def get_cache() -> CacheManager:
    """Get the global cache instance."""
    return _GlobalCache
