"""
Distributed sliding-window rate limiter backed by Redis.
Each (key, window) pair uses two Redis keys:
    rate:{key}:{window_id}       - counter for the current window
    rate:{key}:{window_id - 1}   - counter for the previous window
The effective count is:
    prev_count * (1 - elapsed_fraction) + current_count
This smooths out bursts at window boundaries.
"""

import time
import redis.asyncio as redis


async def is_rate_limited(
    r: redis.Redis,
    key: str,
    limit: int,
    window_secs: int,
) -> tuple[bool, dict[str, str]]:
    """
    Returns (is_limited, info_dict).
    info_dict contains remaining, limit, reset_at for response headers.
    """
    now = time.time()
    window_id = int(now // window_secs)
    window_start = window_id * window_secs
    elapsed = now - window_start
    fraction_elapsed = elapsed / window_secs

    curr_key = f"rate:{key}:{window_id}"
    prev_key = f"rate:{key}:{window_id-1}"

    # our rate limiter counts all requests: successful and dropped
    pipe = r.pipeline(
        transaction=True
    )  # when transaction is true, all queued commands are exec together
    pipe.get(prev_key)
    pipe.incr(curr_key)
    pipe.expire(
        curr_key, window_secs * 2
    )  # removes the `curr_key` key after `window_secs*2` time
    results = await pipe.execute()

    prev_count = int(results[0] or 0)
    curr_count = int(results[1])

    # weighted count using sliding window approx
    effective = prev_count * (1 - fraction_elapsed) + curr_count

    remaining = max(0, limit - int(effective))
    reset_at = window_start + window_secs

    info = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(int(reset_at)),
    }
    return effective > limit, info
