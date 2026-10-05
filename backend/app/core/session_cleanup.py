from fastapi import Depends
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.core.deps import get_db
from app.services.auth_service import AuthService

auth_service = AuthService()


async def cleanup_expired_refresh_tokens() -> int:
    async with AsyncSessionLocal() as session:  # fresh session every pass, not held open
        try:
            deleted = await auth_service.del_expired_refresh_tokens(session=session)
            await session.commit()  # explicit, since we're outside get_db's DI
            return deleted or 0
        except Exception:
            await session.rollback()
            raise


async def run_periodic_cleanup(interval_seconds: int):
    while True:
        try:
            deleted = await cleanup_expired_refresh_tokens()
            ...
        except asyncio.CancelledError:
            raise
        except Exception:
            print("expired-token cleanup failed; will retry next interval")
        await asyncio.sleep(interval_seconds)
