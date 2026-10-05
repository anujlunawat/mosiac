from pydantic import PostgresDsn
from pydantic_settings import BaseSettings

from datetime import timedelta, timezone, datetime
from pathlib import Path

# jwt config
# JWT_SECRET: str = "k9FIhxGL1xqJXeJ4x7H+Ja2XU+01QBB4unzZcjK7/YE="
jwt_timeout = timedelta(minutes=15)
jwt_algorithm = "HS256"

# logging
app_dir = Path(__file__).resolve().parent
log_filepath = app_dir / "logging" / "logs" / "server.log"

# cookie
ACCESS_TTL = timedelta(minutes=10)  # ttl=time to live
REFRESH_TTL = timedelta(days=30)  # sliding: every refresh issues a fresh 30 days
REUSE_GRACE = timedelta(seconds=10)
TICKET_TTL_SECONDS = 30
COOKIE_NAME = "refresh_token"
COOKIE_PATH = "auth"  # browser only sends it to /auth/*
COOKIE_SECURE = True  # only sends the cookie over HTTPS connection
TOKEN_CLEANUP_INTERVAL_SECONDS = 3600

# y-websocket status codes
# y-websocket (v3) will NOT auto-retry on 4400-4499, it fires a 'closed' event instead,
# which is exactly what the client uses to fetch a new ticket / stop.
WS_UNAUTHORIZED = (
    4401  # ticket missing / expired / already used -> client fetches a new ticket
)
WS_FORBIDDEN = 4403  # user has no access to this doc-> client shows "no access"
ACCESS_RECHECK_SECONDS = 60

# allowed origins
# ALLOWED_ORIGINS = [
#     "http://localhost:5173",
#     "http://192.168.56.1:5173",
#     "http://192.168.1.7:5173",
#     "http://172.20.176.1:5173",
#     "*",
#     "http://localhost",
# ]


class Settings(BaseSettings):
    # dialect+driver://username:password@host:port/database
    DATABASE_URL: str = (
        "postgresql+asyncpg://collabdocs:secret@localhost:5432/collabdocs"
    )
    REDIS_URL: str = "redis://localhost:6379"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_SECRET: str = "k9FIhxGL1xqJXeJ4x7H+Ja2XU+01QBB4unzZcjK7/YE="
    ALLOWED_ORIGINS: list[str]


settings = Settings()
