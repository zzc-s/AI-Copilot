import time


class SimpleTTLCache:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, object]] = {}

    def get(self, key: str) -> object | None:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: object) -> None:
        self._store[key] = (time.time() + self.ttl_seconds, value)
