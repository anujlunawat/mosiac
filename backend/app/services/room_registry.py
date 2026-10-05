"""
Room lifecycle for the collaborative editor.

Solves four problems in one place:
  1. Load-from-DB happens exactly once per *live* room (no `len(room.clients) == 0` guessing).
  2. A client that joins while the last user is leaving cannot end up in a deleted room
     (per-document lock + our own reference count instead of `room.clients`).
  3. Edits are persisted every few seconds while people are typing, not only on last-leave.
  4. If the final save fails, the room stays in memory (nothing is lost) and the autosave
     loop keeps retrying; the room is deleted only after a successful save.

Works with pycrdt-websocket 0.15.x / 0.16.x (verified: `WebsocketServer.delete_room` is a
coroutine and keyword-only, and `YRoom` does NOT load YStore contents by itself).
"""

from __future__ import annotations

import uuid
import asyncio
import logging
import weakref
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import Callable, Awaitable
from typing import TYPE_CHECKING


from app.db.redis import get_redis_binary

if TYPE_CHECKING:
    from pycrdt.websocket import WebsocketServer
    from pycrdt.websocket.yroom import YRoom

log = logging.getLogger(__name__)

LoadFn = Callable[[str], Awaitable[bytes | None]]
SaveFn = Callable[[str, bytes], Awaitable[None]]


class RoomRegistry:
    def __init__(
        self,
        server: "WebsocketServer",
        load: LoadFn,
        save: SaveFn,
        autosave_every: float = 5.0,
    ) -> None:
        self._server = server
        self._load = load
        self._save = save
        self._autosave_every = autosave_every

        # one lock per doc, gc collects automatically when nobody uses it
        self._locks: weakref.WeakValueDictionary[str, asyncio.Lock] = (
            weakref.WeakValueDictionary()
        )
        self._refs: dict[str, int] = {}  # connections per doc
        self._dirty: set[str] = set()  # docs with unsaved changes
        self._autosave_tasks: dict[str, asyncio.Task] = {}
        self._subscriptions: dict[str, object] = {}
        self._applying_remote: set[str] = (
            set()
        )  # doc ids currently applying remote updates

        self._redis_subscriptions: dict[str, asyncio.Task] = {}
        self._get_redis_channel = lambda doc_id: f"doc:{doc_id}"
        self._latest_published_state: dict[str, bytes] = {}

        self._instance_id: bytes = uuid.uuid4().bytes

    # ------------------------------------------------------------------ helpers

    def _lock(self, doc_id: str) -> asyncio.Lock:
        lock = self._locks.get(doc_id)
        if lock is None:
            lock = self._locks[doc_id] = asyncio.Lock()
        return lock

    async def _dispose(self, doc_id: str, room: "YRoom") -> None:
        """Remove a saved, unused room. Caller must hold the doc lock."""
        sub = self._subscriptions.pop(doc_id, None)
        if sub is not None:
            room.ydoc.unobserve(sub)
        task = self._autosave_tasks.pop(doc_id, None)
        if task is not None and task is not asyncio.current_task():
            task.cancel()
        self._dirty.discard(doc_id)

        # Cancel Redis subscription
        redis_task = self._redis_subscriptions.pop(doc_id, None)
        if redis_task is not None:
            redis_task.cancel()
        self._latest_published_state.pop(doc_id, None)

        await self._server.delete_room(name=doc_id)

    # --------------------------------------------------------------- public API
    async def acquire(self, doc_id: str) -> "YRoom":
        """Call before `room.serve()`. Returns a room whose ydoc is already loaded."""
        async with self._lock(doc_id):
            # if the room does not exists.
            # NOTE: this does not mean that the doc_id does not exist in the db.
            fresh = doc_id not in self._server.rooms
            room = await self._server.get_room(doc_id)

            if fresh:
                try:
                    state = await self._load(doc_id)
                    if state:
                        room.ydoc.apply_update(state)
                    self._latest_published_state[doc_id] = room.ydoc.get_state()
                except BaseException:
                    # never leave a half-established (empty) room behind
                    # the next client would be served a blank doc
                    await self._server.delete_room(name=doc_id)
                    self._latest_published_state.pop(doc_id)
                    raise

                # subscribe to channel
                self._redis_subscriptions[doc_id] = asyncio.create_task(
                    self._subscribe(channel=self._get_redis_channel(doc_id), room=room)
                )

                # def cb(_event, d=doc_id):
                #     asyncio.create_task(self._doc_update(d))

                # observe the room only after loading.
                self._subscriptions[doc_id] = room.ydoc.observe(
                    # lambda _event, d=doc_id: self._dirty.add(d)
                    lambda event, d=doc_id: (
                        None
                        if d in self._applying_remote
                        else asyncio.create_task(self._doc_update(d))
                    )
                )
                self._autosave_tasks[doc_id] = asyncio.create_task(
                    self._autosave(doc_id, room)
                )

            self._refs[doc_id] = self._refs.get(doc_id, 0) + 1
            return room

    async def release(self, doc_id: str, room: YRoom) -> None:
        """
        Called in `finally` after `room.serve()` returns (or raises).
        """
        # async with self._locks[doc_id]:
        async with self._lock(doc_id):
            remaining = self._refs.get(doc_id, 0) - 1
            if remaining > 0:
                self._refs[doc_id] = remaining
                return
            self._refs.pop(doc_id, None)

            try:
                await self._save(doc_id, room.ydoc.get_update())
            except Exception:
                # keep the room (and its unsaved state) in memory; autosave will try.
                # and dispose off the room once a save succeeds
                log.exception(
                    "final save failed for %s; keeping room in memory", doc_id
                )
                self._dirty.add(doc_id)
                return
            await self._dispose(doc_id, room)

    async def flush_all(self) -> None:
        """Call from the FastAPI lifespan on shutdown, before leaving `async with server`."""
        for doc_id, room in list(self._server.rooms.items()):
            async with self._lock(doc_id):
                try:
                    await self._save(doc_id, room.ydoc.get_update())
                except Exception:
                    log.exception("flush failed for %s", doc_id)

    # ---------------------------------------------------------------- autosave

    async def _autosave(self, doc_id: str, room: "YRoom") -> None:
        while True:
            await asyncio.sleep(self._autosave_every)
            if doc_id not in self._dirty:
                continue
            async with self._lock(doc_id):
                if self._server.rooms.get(doc_id) is not room:
                    return  # room was disposed while we waited for the lock

                try:
                    await self._save(doc_id, room.ydoc.get_update())
                except Exception:
                    # self._dirty.add(doc_id)
                    log.exception("autosave failed for %s (will retry)", doc_id)
                    continue

                self._dirty.discard(doc_id)
                if self._refs.get(doc_id, 0) == 0:
                    # A failed final save left this room orphaned; now it's safe to drop.
                    await self._dispose(doc_id, room)
                    return

    # ------------------------------------------------------------ redis pub/sub
    async def _subscribe(self, channel: str, room: YRoom):
        r = await get_redis_binary()
        pubsub = r.pubsub()
        # subscribe to the channel
        await pubsub.subscribe(channel)
        doc_id = self._server.get_room_name(room)
        async for msg in pubsub.listen():
            if msg["type"] != "message":
                continue
            data = msg["data"]
            sender_id = data[:16]  # the first 16 bytes are instance id
            update = data[16:]  # the actual yjs update

            if sender_id == self._instance_id:
                continue
            self._applying_remote.add(doc_id)
            if data:
                room.ydoc.apply_update(update)
            self._applying_remote.remove(doc_id)

    async def _publish(self, channel: str, msg: bytes):
        r = await get_redis_binary()
        # add the instance id to the msg
        await r.publish(channel=channel, message=self._instance_id + msg)

    async def _doc_update(self, doc_id: str):
        if doc_id in self._applying_remote:
            return  # Don't re-publish updates received from Redis
        # add the doc_id to _dirty
        self._dirty.add(doc_id)
        # publish the msg
        latest = self._latest_published_state.get(doc_id, None)
        room = await self._server.get_room(doc_id)
        await self._publish(
            self._get_redis_channel(doc_id), room.ydoc.get_update(latest)
        )
        self._latest_published_state[doc_id] = room.ydoc.get_state()
