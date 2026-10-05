"""
the purpose was to create TicketStore as a singleton.
but, the old arch:
    def __new__(cls, ttl: int = config.TICKET_TTL_SECONDS):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ttl: int = config.TICKET_TTL_SECONDS) -> None:
        self._ttl = ttl
        self._items: dict[str, tuple[str, str, float]] = {}
would have caused bugs. WHY? lets understand the flow.
when TicketStored() the first time, __new__ gets called, _instance is None, hence new class instance is created and returned. then this instance is passed to __init__. which creates 2 the attributes on instance: _ttl and _items.
Now, when TicketStore() is called the second time, __new__ return the _instance created earlier, this gets passed to __init__. here, __init__ created 2 attr for the instance again. THIS WOULD CLEAR THE _items DICT. hence, added that part to __new__ and commented out __init__.

----------------------------------------------------------------------------------

`redis.getdel(): getdel is a single Redis command that atomically reads and deletes the key. This guarantees that a ticket can only be used exactly once, even if two backend instances try to redeem it at the exact same millisecond. An attacker cannot replay a stolen ticket.
"""

import secrets
import time

import app.config as config
from app.db.redis import get_redis


class TicketStore:
    """
    Single-use, short-lived, bound to (user, doc).  In-memory => only valid with ONE worker process.

    Multi-worker version with Redis (same interface):
        issue : await r.set(f"wst:{t}", f"{user_id}|{doc_id}", ex=TICKET_TTL_SECONDS)
        redeem: v = await r.getdel(f"wst:{t}")          # atomic get+delete => single use
    """

    _instance = None
    get_key = lambda self, ticket: f"wst:{ticket}"

    def __new__(cls, ttl: int = config.TICKET_TTL_SECONDS):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._ttl = ttl
            # cls._items: dict[str, tuple[str, str, float]] = {}
        return cls._instance

    # def __init__(self, ttl: int = config.TICKET_TTL_SECONDS) -> None:
    #     self._ttl = ttl
    #     self._items: dict[str, tuple[str, str, float]] = {}

    async def issue(self, user_id: str, doc_id: str) -> str:
        r = await get_redis()
        ticket = secrets.token_urlsafe(32)
        await r.set(
            self.get_key(ticket),
            f"{user_id}|{doc_id}",
            ex=self._ttl,
        )
        return ticket

    async def redeem(self, ticket: str, doc_id: str) -> str | None:
        r = await get_redis()
        val: str | None = await r.getdel(
            self.get_key(ticket)
        )  # atomic get + del (single use)
        if val is None:
            return None
        user_id, ticket_doc = val.split("|", 1)  # split the val on "|", 1 time
        if ticket_doc != doc_id:
            return None
        return user_id


tickets = TicketStore()
