# CollabDocs

A scalable, real-time collaborative document editor built with React, FastAPI, Yjs (CRDT), and PostgreSQL.

## Features
- Real-time collaboration using Yjs (CRDTs).
- Secure JWT-based Authentication with Refresh Token rotation.
- WebSocket ticketing system for authorized document access.
- Auto-saving & scalable document versioning in PostgreSQL.
- Distributed Rate Limiting via Redis.

## Tech Stack
- **Frontend**: React, TypeScript, Vite, TailwindCSS (or Vanilla CSS)
- **Backend**: Python, FastAPI, SQLAlchemy (Async), Uvicorn
- **CRDT / Real-time**: yjs (frontend), pycrdt & pycrdt-websocket (backend)
- **Infrastructure**: Docker, PostgreSQL, Redis

## Quick Start
1. `docker-compose up -d` to start PostgreSQL and Redis.
2. Backend: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload`
3. Frontend: `cd frontend && npm install && npm run dev`
