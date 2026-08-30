import asyncio
import time
from dataclasses import dataclass


@dataclass
class Bucket:
    tokens: float
    last_refill: float


class RateLimiter:
    """Simple in-memory token-bucket rate limiter."""

    def __init__(
        self,
        capacity: int = 20,
        refill_rate: float = 1.0,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero.")

        if refill_rate <= 0:
            raise ValueError("refill_rate must be greater than zero.")

        self._capacity = float(capacity)
        self._refill_rate = refill_rate
        self._buckets: dict[str, Bucket] = {}
        self._lock = asyncio.Lock()

    async def allow(self, user_id: str) -> bool:
        now = time.monotonic()

        async with self._lock:
            bucket = self._buckets.get(user_id)

            if bucket is None:
                self._buckets[user_id] = Bucket(
                    tokens=self._capacity - 1,
                    last_refill=now,
                )
                return True

            elapsed = now - bucket.last_refill

            bucket.tokens = min(
                self._capacity,
                bucket.tokens + elapsed * self._refill_rate,
            )
            bucket.last_refill = now

            if bucket.tokens < 1:
                return False

            bucket.tokens -= 1
            return True


rate_limiter = RateLimiter(
    capacity=20,
    refill_rate=1.0,
)