from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import settings

# engine = create_async_engine(url=DATABASE_URL, echo=True)
engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=False,
    pool_size=10,  # 10 persistent connections kept open
    max_overflow=20,  # up to 20 extra connections under burst load
    pool_timeout=30,  # wait up to 30s for a free connection before raising an error. if all connections are busy, then wait for this time for any connection to get free before raising error
    pool_recycle=1800,  # close and recreate connections every 30 min
    # (prevents stale connections after DB restarts)
    pool_pre_ping=True,  # before using a connection, send a lightweight "SELECT 1"
    # to verify it's still alive. prevents "connection reset" errors.
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
