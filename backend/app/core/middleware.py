import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class InMemoryRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.time()
        queue = self.requests[key]
        while queue and queue[0] < now - self.window_seconds:
            queue.popleft()
        if len(queue) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Too many requests")
        queue.append(now)


rate_limiter = InMemoryRateLimiter()


async def rate_limit_dependency(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    rate_limiter.check(client)
