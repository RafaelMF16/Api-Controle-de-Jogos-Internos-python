from threading import Lock
from time import monotonic
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class MemoryCache:
    def __init__(self) -> None:
        self._values: dict[str, tuple[float, object]] = {}
        self._lock = Lock()

    def get_or_set(self, key: str, ttl_seconds: int, factory: Callable[[], T]) -> T:
        now = monotonic()

        with self._lock:
            cached = self._values.get(key)
            if cached and cached[0] > now:
                return cached[1]  # type: ignore[return-value]

        value = factory()

        with self._lock:
            self._values[key] = (now + max(ttl_seconds, 0), value)

        return value

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._values.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            keys = [key for key in self._values if key.startswith(prefix)]
            for key in keys:
                self._values.pop(key, None)
