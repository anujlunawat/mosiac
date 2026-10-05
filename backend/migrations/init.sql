-- ──────────────────────────────────────────────────────────────────────────
-- CollabDocs — Initial Schema
-- Runs automatically on first `docker-compose up` via docker-entrypoint-initdb.d
-- ──────────────────────────────────────────────────────────────────────────
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- ── Users ─────────────────────────────────────────────────────────────────────
-- Stores registered accounts. password_hash is NULL for OAuth users.
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT,
    -- bcrypt hash; NULL if OAuth
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- ── Documents ─────────────────────────────────────────────────────────────────
-- For MVP: one shared document with id = 'shared-doc'.
-- yjs_state stores the full serialised Yjs document as binary (BYTEA).
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY DEFAULT 'shared-doc',
    title TEXT NOT NULL DEFAULT 'Shared Document',
    owner_id UUID REFERENCES users(id) ON DELETE
    SET NULL,
        yjs_state BYTEA,
        -- latest full Yjs snapshot
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- ── Document Version History ───────────────────────────────────────────────
-- Each row is one incremental Yjs update (binary delta).
-- Replay all rows in order to reconstruct any past state.
CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    yjs_update BYTEA NOT NULL,
    -- incremental Yjs binary delta
    created_by UUID REFERENCES users(id) ON DELETE
    SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_doc_versions_doc_id ON document_versions(doc_id, created_at);
-- ── Document Collaborator ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_collaborators (
    doc_id TEXT NOT NULL,
    user_id UUID NOT NULL,
    role TEXT NOT NULL DEFAULT 'editor',
    invited_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (doc_id, user_id),
    CONSTRAINT fk_document_collaborators_document FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_document_collaborators_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_document_collaborators_invited_by FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE
    SET NULL
);
-- Index for efficient lookup by user
CREATE INDEX ix_document_collaborators_user ON document_collaborators (user_id);
-- ── Refresh Tokens ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    family_id UUID NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    CONSTRAINT fk_refresh_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
-- Indexes
CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX ix_refresh_tokens_family_id ON refresh_tokens (family_id);
-- ── Seed: insert the single shared document ────────────────────────────────
INSERT INTO documents (id, title)
VALUES ('shared-doc', 'Shared Document') ON CONFLICT (id) DO NOTHING;