import asyncio
import contextlib
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import Depends, Query
from fastapi import HTTPException, status

from app.schemas.ticket_store import tickets
import app.config as config
from app.routes.auth import current_user_id
from app.core.ws_server import websocket_server
from app.services.room_registry import RoomRegistry
from app.db.database import AsyncSessionLocal
from app.services.document_service import DocumentService
from app.schemas.enums import SyncMessagetype, MessageType
from app.config import settings
from app.db.redis import get_redis
from app.core.rate_limiter import is_rate_limited

router = APIRouter()
doc_service = DocumentService()


# ------------------------------------------------------------ persistence glue
async def _load(doc_id: str) -> bytes | None:
    async with AsyncSessionLocal() as session:
        doc = await doc_service.get_doc(session=session, doc_id=doc_id)
    return doc.yjs_state if doc and doc.yjs_state else None


async def _save(doc_id: str, data: bytes) -> None:
    async with AsyncSessionLocal() as session:
        try:
            await doc_service.save_snapshot(
                session=session, doc_id=doc_id, yjs_bytes=data
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# # ------------------------------------------------------------ redis pub/sub
# async def _subscribe(channel: str, doc_id: str):
#     r = await get_redis()
#     pubsub = r.pubsub()
#     # subscribe to the channel
#     await pubsub.subscribe(channel)

#     async for msg in pubsub.listen():


registry = RoomRegistry(websocket_server, load=_load, save=_save, autosave_every=5.0)


class _WSAdapter:
    """
    pycrdt-websocket expects the `Channel` library interface:
        .recv() → bytes
        .send(bytes) → None

    FastAPI's WebSocket has different method names:
        .receive_bytes() → bytes
        .send_bytes(bytes) → None

    This adapter bridges the two.
    """

    def __init__(self, ws: WebSocket):
        self._ws = ws
        self._id = (
            f"{ws.client.host}:{ws.client.port}" if ws.client else "unknown_client"
        )

    async def recv(self) -> bytes:
        return await self._ws.receive_bytes()

    async def send(self, data: bytes) -> None:
        try:
            # msg_type = MessageType(data[0])
            # print(f"[SEND to   {self._id}] {len(data)} bytes ({msg_type.name})")
            # if msg_type == MessageType.SYNC:
            #     print(
            #         f"-------------------------------------> ({SyncMessagetype(data[1]).name})"
            #     )
            # elif msg_type == MessageType.AWARENESS:
            #     start = data.find(b"{")
            #     if start != -1:
            #         print(data[start:].decode("utf-8"))

            await self._ws.send_bytes(data)
        except (WebSocketDisconnect, RuntimeError):
            pass  # peer already gone; its receive loop ends the session

    # this property is actually used as room_name internally
    @property
    def path(self) -> str:
        return str(self._ws.url.path)

    def __aiter__(self):
        return self  # the object itself is the iterator

    async def __anext__(self) -> bytes:
        try:
            data = await self._ws.receive_bytes()
            # msg_type = MessageType(data[0])
            # print(f"[RECV from {self._id}] {len(data)} bytes ({msg_type.name})")

            # if data["type"] == "websocket.disconnect":
            #     raise WebSocketDisconnect
        except (WebSocketDisconnect, RuntimeError):
            raise StopAsyncIteration  # signals "loop is done"

        return data


# -------------------------------------- helpers  --------------------------------------
async def _watch_access(websocket: WebSocket, user_id: str, doc_id: str) -> None:
    """Kick the user out of a live session if their access to the doc is revoked."""
    while True:
        await asyncio.sleep(config.ACCESS_RECHECK_SECONDS)
        try:
            async with AsyncSessionLocal() as session:
                allowed = await doc_service.user_can_access(
                    session=session, doc_id=doc_id, user_id=user_id
                )
        except Exception:
            continue
        if not allowed:
            # the below line means:
            # Try to close the WebSocket connection, but ignore any exceptions that occur while doing so.
            # it is same as:
            # try:
            #     command
            # except Exception:
            #     pass
            with contextlib.suppress(Exception):
                await websocket.close(code=config.WS_FORBIDDEN, reason="access revoked")
            return


async def _shielded(coro) -> None:
    """Run cleanup to completion even if this request task is being cancelled (server shutdown)."""
    task = asyncio.ensure_future(coro)
    try:
        await asyncio.shield(task)
    except asyncio.CancelledError:
        await task
        raise


# ----------------------------------------------------------------------- routes


# NOTE: since websocket dont have request obj passed. hence we cant use the `dependencies` as we used for the auth endpoints!
@router.websocket(
    "/ws/{doc_id}",
)
async def collab_ws(
    websocket: WebSocket,
    doc_id: str,
    ticket: str = Query(...),  # same as Query()
):
    # 1. check origin before accept
    # http headers are case-insensitive
    origin = websocket.headers.get("origin", "").rstrip("/")
    if origin not in settings.ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return

    # ── Rate limit: max 10 WS connections per IP per minute ──
    r = await get_redis()
    ip = websocket.client.host if websocket.client else "unknown"
    limited, _ = await is_rate_limited(r, f"ws-connect:{ip}", limit=10, window_secs=60)
    if limited:
        await websocket.close(code=1008, reason="rate limited")
        return

    # 2. accept the connection so the client can acutally see the close codes (if sent)
    await websocket.accept()
    user_id = await tickets.redeem(ticket, doc_id)
    if user_id is None:
        await websocket.close(
            code=config.WS_UNAUTHORIZED, reason="invalid or expired ticket"
        )
        return

    # 3. join the room
    # loads from DB if this is the first connection for the doc
    try:
        room = await registry.acquire(doc_id)
    except Exception:
        await websocket.close(code=1011)
        return

    watchdog = asyncio.create_task(_watch_access(websocket, user_id, doc_id))

    try:
        await room.serve(_WSAdapter(websocket))
    finally:
        watchdog.cancel()
        await _shielded(
            registry.release(doc_id, room)
        )  # last one out saves + deletes the room


@router.get("/ws/{doc_id}/users")
async def get_room_users(doc_id: str, user_id: str = Depends(current_user_id)):
    async with AsyncSessionLocal() as session:
        if not await doc_service.user_can_access(session, user_id, doc_id):
            raise HTTPException(403, "no access to this document")
    # room = websocket_server.rooms.get(
    #     doc_id
    # )  # .get(): never creates a room as a side effect
    # return {"num_connections": len(room.clients) if room else 0}

    return {"num_connections": registry._refs.get(doc_id, 0)}
