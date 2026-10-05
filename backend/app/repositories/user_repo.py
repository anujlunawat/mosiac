from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User


class UserRepository:

    async def create(
        self, *, session: AsyncSession, email: str, name: str, password_hash: str | None
    ) -> User:
        user = User(email=email, name=name, password_hash=password_hash)

        session.add(user)
        await session.flush()

        return user

    async def get(self, *, session: AsyncSession, user_id: UUID) -> User | None:
        # statement
        stmt = select(User).where(User.id == user_id)
        return await session.scalar(stmt)

    async def get_by_email(self, *, session: AsyncSession, email: str) -> User | None:
        # returns None if no user present with the given email
        stmt = select(User).where(User.email == email)
        return await session.scalar(stmt)

    async def list(self, session: AsyncSession) -> list[User]:
        stmt = select(User)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, *, session: AsyncSession, user: User) -> None:
        await session.delete(user)
