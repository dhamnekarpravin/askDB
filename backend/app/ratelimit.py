import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from . import config

_hits: dict[str, deque] = defaultdict(deque)


async def rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = _hits[ip]

    # Drop timestamps that are outside the window
    while window and now - window[0] > config.RATE_LIMIT_WINDOW_SECONDS:
        window.popleft()

    if len(window) >= config.RATE_LIMIT_MAX:
        retry = int(config.RATE_LIMIT_WINDOW_SECONDS - (now - window[0])) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Try again in {retry} seconds",
            headers={"Retry-After": str(retry)},
        )
    window.append(now)