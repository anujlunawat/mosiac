from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session  # ← request handler runs here
            await session.commit()  # ← auto-commit if no exception
        except Exception:
            await session.rollback()  # ← undo everything if something blew up
            raise
