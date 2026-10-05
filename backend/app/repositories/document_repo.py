from uuid import UUID

from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func


from app.models.models import Document, DocumentVersion, DocumentCollaborator, Base


class DocumentRepository:

    # get the document from doc_id
    async def get(self, *, session: AsyncSession, doc_id: str) -> Document | None:
        stmt = select(Document).where(Document.id == doc_id)
        return await session.scalar(stmt)

    async def save_snapshot(
        self, *, session: AsyncSession, doc_id: str, yjs_bytes: bytes
    ) -> None:

        stmt = (
            update(Document)
            .where(Document.id == doc_id)
            .values(
                yjs_state=yjs_bytes,
                updated_at=func.now(),
            )
        )

        await session.execute(stmt)
        # session.flush()
        # return yjs_bytes

    async def append_version(
        self, *, session: AsyncSession, doc_id: str, delta: bytes, user_id: UUID
    ) -> None:

        stmt = insert(DocumentVersion).values(
            doc_id=doc_id, yjs_update=delta, created_by=user_id
        )
        await session.execute(stmt)

    async def get_collaborator_row(
        self, *, session: AsyncSession, doc_id: str, user_id: UUID
    ):
        stmt = select(DocumentCollaborator).where(
            DocumentCollaborator.user_id == user_id,
            DocumentCollaborator.doc_id == doc_id,
        )

        return (await session.execute(stmt)).scalar_one_or_none()

    def add_collaborator_row(
        self,
        *,
        session: AsyncSession,
        doc_id: str,
        user_id: UUID,
    ) -> None:
        session.add(
            DocumentCollaborator(
                doc_id=doc_id,
                user_id=user_id,
                role="editor",
            )
        )
