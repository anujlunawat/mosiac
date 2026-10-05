from fastapi import Request, HTTPException, status, Depends
from redis.exceptions import MaxConnectionsError

from app.db.redis import get_redis
from app.core.rate_limiter import is_rate_limited


def rate_limit(limit: int, window_secs: int, key_func=None):
    """
    factory that returns a fastapi dependency.

    Args:
        limit:    max requests per window
        window:   window size in seconds
        key_func: optional callable(request) -> str to customize the key
    """

    async def _dependency(request: Request):
        r = await get_redis()

        if key_func:
            identifier = key_func(request)
        else:
            # client.host is the ip addr of the client
            identifier = request.client.host if request.client else "unknown"
        # url.path is the endpoint path that the client has made a call to
        path = request.url.path
        key = f"{path}: {identifier}"

        try:
            limited, info = await is_rate_limited(r, key, limit, window_secs)
        except MaxConnectionsError:
            print("max connections reached")
            raise Exception()

        if limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. please try again later",
                headers=info,
            )

        # attach info to the response (via state, picked up by the middleware)
        request.state.rate_limit_headers = info

    return _dependency
