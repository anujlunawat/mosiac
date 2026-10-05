# __all__ = ["DocumentService"]
from __future__ import annotations
from typing import TYPE_CHECKING

from app.repositories.document_repo import DocumentRepository
from app.models.models import Document, DocumentVersion, DocumentCollaborator

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import UUID


class DocumentService:
    def __init__(self):
        self.repo = DocumentRepository()

    async def get_doc(
        self,
        session: AsyncSession,
        doc_id: str,
    ) -> Document | None:
        return await self.repo.get(session=session, doc_id=doc_id)

    async def save_snapshot(
        self, session: AsyncSession, doc_id: str, yjs_bytes: bytes
    ) -> None:
        return await self.repo.save_snapshot(
            session=session, doc_id=doc_id, yjs_bytes=yjs_bytes
        )

    async def append_doc_version(
        self,
        session: AsyncSession,
        doc_id: str,
        delta: bytes,
        user_id: UUID,
    ) -> None:
        return await self.repo.append_version(
            session=session, doc_id=doc_id, delta=delta, user_id=user_id
        )

    async def user_can_access(
        self,
        session: AsyncSession,
        doc_id: str,
        user_id: UUID,
    ) -> bool:
        row = await self.repo.get_collaborator_row(
            session=session, doc_id=doc_id, user_id=user_id
        )
        return row is not None

    def give_user_access(
        self,
        session: AsyncSession,
        doc_id: str,
        user_id: UUID,
    ):
        self.repo.add_collaborator_row(
            session=sessions,
            doc_id=doc_id,
            user_id=user_id,
        )
