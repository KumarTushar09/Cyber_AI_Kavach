import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


async def retry_async(
    fn: Callable[[], Awaitable[Any]],
    attempts: int,
    base_delay_seconds: float,
    retry_on: tuple[type[BaseException], ...],
) -> Any:
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except retry_on as exc:
            last_exc = exc
            if attempt >= attempts:
                break
            delay = base_delay_seconds * (2 ** (attempt - 1))
            await asyncio.sleep(delay)

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("retry_async reached unexpected state")
