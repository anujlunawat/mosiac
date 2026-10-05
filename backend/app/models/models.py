import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID, BYTEA, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy import Text, ForeignKey, String, text, Index
from sqlalchemy import DateTime
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    # server_default tells SQLAlchemy the database server (not Python) will provide a default value if none is supplied during an INSERT
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(__type_pos=Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(__type_pos=Text, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # DateTime is a sqlAlchemy col type
    # what does server_default=func.now() mean here?
    # When a row is inserted and created_at isn't provided, let the database execute NOW()
    # using the `default` arg uses the python's clock. `func.now()` uses the database's clock


# this table is capable of storing mutiple documents, but we store just one.
class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, server_default=text("'shared_doc'")
    )
    title: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'Shared Document'")
    )
    owner_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    yjs_state: Mapped[bytes | None] = mapped_column(BYTEA)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    doc_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    yjs_update: Mapped[bytes | None] = mapped_column(BYTEA, nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DocumentCollaborator(Base):
    """
    Who can open which room, and with what role. This is the table `user_can_access`
    (used when issuing a WebSocket ticket, and by the periodic in-session access
    re-check) should query. The document's owner is just a row here with role='owner',
    inserted when the document is created -- there's no separate special case.
    """

    __tablename__ = "document_collaborators"

    doc_id: Mapped[str] = mapped_column(
        Text, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'editor'")
    )  # owner | editor | viewer
    invited_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_document_collaborators_user", "user_id"),)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
