from sqlalchemy import select, update, insert, delete
from typing import TYPE_CHECKING

from app.models.models import RefreshToken
from app.utils import _hash, _utcnow
from app.config import REFRESH_TTL

if TYPE_CHECKING:
    from datetime import datetime
    from sqlalchemy.ext.asyncio import AsyncSession


class RefreshRepository:
    def __init__(self):
        pass

    async def get_row(
        self, *, session: AsyncSession, token_hash: str, for_update: bool = True
    ) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)

        if for_update:
            # with_for_update(): im about to modify this row. lock it so nobody else can modify it until my transaction finishes
            stmt = stmt.with_for_update()

        return (await session.execute(stmt)).scalar_one_or_none()

    async def delete_family(self, *, session: AsyncSession, family_id: str) -> None:
        stmt = delete(RefreshToken).where(RefreshToken.family_id == family_id)
        await session.execute(stmt)

    def create_row(
        self, *, session: AsyncSession, user_id: str, family_id: str, raw: str
    ) -> None:
        session.add(
            RefreshToken(
                user_id=user_id,
                family_id=family_id,
                token_hash=_hash(raw),
                expires_at=_utcnow() + REFRESH_TTL,
            )
        )

    async def del_expired_tokens(
        self, *, session: AsyncSession, _after: "datetime"
    ) -> None:
        stmt = delete(RefreshToken).where(RefreshToken.expires_at < _after)
        await session.execute(stmt)
