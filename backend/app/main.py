import asyncio
from contextlib import asynccontextmanager
import contextlib
from fastapi import FastAPI, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text

from app.core.rate_deps import rate_limit
from app.core.ws_server import websocket_server
from app.core.session_cleanup import run_periodic_cleanup
from app.ws.collab import registry
from app.db.database import engine, AsyncSessionLocal
from app.models.models import Base
from app.routes.auth import router as auth_router
from app.ws.collab import router as ws_router
from app.config import settings, TOKEN_CLEANUP_INTERVAL_SECONDS
from app.db.redis import get_redis, get_redis_binary, close_redis, close_redis_binary


@asynccontextmanager
async def lifespan(app: FastAPI):
    # creates the postgres tables. doesnt throw error if table already present
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)

    # warm up the pool
    await get_redis()
    await get_redis_binary()

    cleanup_task = asyncio.create_task(
        run_periodic_cleanup(TOKEN_CLEANUP_INTERVAL_SECONDS)
    )
    async with websocket_server:
        yield
        await registry.flush_all()

    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task

    await close_redis()  # shutdown
    await close_redis_binary()


class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        headers: dict | None = getattr(request.state, "rate_limit_headers", None)

        if headers:
            for k, v in headers.items():
                response.headers[k] = v
        return response


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(ws_router)

# `CORSMiddleware` only handles http cors requests such as get, post, put, delete etc.
# websockt connections use an http upgrade handshake
# this handshake does not go through cors validation
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitHeaderMiddleware)


@app.get("/benchmark", dependencies=[Depends(rate_limit(limit=50, window_secs=1))])
async def benchmark():
    # await asyncio.sleep(0.5)
    return {"success": "true"}


@app.get("/")
async def health():
    checks = {}

    # check postgres
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("SELECT 1")
            )  # this commands acts as a lightweight db ping
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"
    # check redis
    try:
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        content={"status": "healthy" if all_ok else "degraded", "checks": checks},
        status_code=(
            status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
    )
