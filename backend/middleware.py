import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.config import settings

logger = logging.getLogger("cyberkavach")
PUBLIC_PATHS = {"/health"}
_rate_limit_lock = asyncio.Lock()
_rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)


def _parse_scopes(raw_scopes: str) -> set[str]:
    return {scope.strip() for scope in raw_scopes.split(",") if scope.strip()}


def _rate_limit_identifier(request: Request) -> str:
    configured_api_key = settings.API_KEY.strip()
    if configured_api_key:
        provided = request.headers.get(settings.AUTH_HEADER_NAME, "")
        if provided == configured_api_key:
            return "api-key:default"
    return f"ip:{request.client.host if request.client else 'unknown'}"


async def _check_rate_limit(identifier: str) -> tuple[bool, int, int]:
    now = time.time()
    window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS

    async with _rate_limit_lock:
        bucket = _rate_limit_buckets[identifier]
        while bucket and bucket[0] <= window_start:
            bucket.popleft()

        if len(bucket) >= settings.RATE_LIMIT_REQUESTS:
            retry_after = max(1, int(bucket[0] + settings.RATE_LIMIT_WINDOW_SECONDS - now))
            return False, 0, retry_after

        bucket.append(now)
        remaining = max(0, settings.RATE_LIMIT_REQUESTS - len(bucket))
        return True, remaining, 0


def reset_rate_limit_state() -> None:
    _rate_limit_buckets.clear()


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(message)s",
    )


def _json_log(message: dict) -> None:
    logger.info(json.dumps(message, default=str))


async def request_context_middleware(request: Request, call_next):
    start = time.time()
    request_id = str(uuid4())
    request.state.request_id = request_id
    request.state.api_scopes = set()
    rate_limit_remaining = None

    if request.url.path not in PUBLIC_PATHS:
        # URL-only local mode: skip auth and rate limiting so local testing stays frictionless.
        if request.url.path.startswith(f"{settings.API_PREFIX}/analyze/url"):
            pass
        else:
            auth_header_name = settings.AUTH_HEADER_NAME
            configured_api_key = settings.API_KEY.strip()
            if configured_api_key:
                provided = request.headers.get(auth_header_name, "")
                if provided != configured_api_key:
                    return JSONResponse(
                        status_code=401,
                        content={
                            "status": "error",
                            "trace_id": request_id,
                            "data": {},
                            "errors": [{"code": "AUTH_REQUIRED", "message": "Missing or invalid API key."}],
                        },
                    )

                request.state.api_scopes = _parse_scopes(settings.API_KEY_SCOPES)

            if settings.RATE_LIMIT_ENABLED:
                allowed, remaining, retry_after = await _check_rate_limit(_rate_limit_identifier(request))
                if not allowed:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "status": "error",
                            "trace_id": request_id,
                            "data": {},
                            "errors": [{"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests."}],
                        },
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                            "X-RateLimit-Remaining": "0",
                        },
                    )
                rate_limit_remaining = remaining

    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    response.headers["X-Request-ID"] = request_id
    if rate_limit_remaining is not None:
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_remaining)

    _json_log(
        {
            "event": "request_completed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client": request.client.host if request.client else None,
        }
    )
    return response
