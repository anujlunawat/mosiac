import uvicorn
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Header
from typing import Any, List


from app.schemas.ticket_store import tickets
import app.config as config

from app.schemas.schemas import UserCreate, UserLogin, TicketRequest
from app.core.security import decode_access_token
from app.core.deps import get_db
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService
from app.core.rate_deps import rate_limit

router = APIRouter(prefix="/auth", tags=["Authentication"])

auth_service = AuthService()
doc_service = DocumentService()


# Ticket endpoint: per-user limiting (needs the user ID from the token)
def _user_key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        from app.core.security import decode_access_token

        try:
            payload = decode_access_token(auth[7:])
            return f"user:{payload['sub']}"
        except Exception:
            pass
    return request.client.host if request.client else "unknown"


def current_user_id(authorization: str | None = Header(default=None)) -> str:
    """FastAPI dependency: `Authorization: Bearer <access token>` -> user id."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer token")
    try:
        payload = decode_access_token(authorization[7:])
    except JWTError:
        raise HTTPException(401, "invalid or expired token")
    return payload["sub"]


# the list of `dependencies` contains Depends objs that have funcs. those funcs are run everytime the endpoint is called; the result of the function is ignored.
@router.post("/register", dependencies=[Depends(rate_limit(limit=50, window_secs=60))])
async def register(
    request: UserCreate, response: Response, session: AsyncSession = Depends(get_db)
):
    return await auth_service.register(session, request, response)


@router.post("/login", dependencies=[Depends(rate_limit(limit=10, window_secs=60))])
async def login(
    request: UserLogin, response: Response, session: AsyncSession = Depends(get_db)
):
    return await auth_service.login(session, request, response)


@router.post("/logout", dependencies=[Depends(rate_limit(limit=20, window_secs=60))])
async def logout(request: Request, session: AsyncSession = Depends(get_db)):
    return await auth_service.logout(session, request)


@router.post("/refresh", dependencies=[Depends(rate_limit(limit=20, window_secs=60))])
async def refresh(
    request: Request, response: Response, session: AsyncSession = Depends(get_db)
):
    return await auth_service.refresh(
        session=session, request=request, response=response
    )


@router.post(
    "/ws-ticket",
    dependencies=[Depends(rate_limit(limit=30, window_secs=60, key_func=_user_key))],
)
async def ws_ticket(
    body: TicketRequest,
    user_id: str = Depends(current_user_id),
    session: AsyncSession = Depends(get_db),
):
    if not await doc_service.user_can_access(
        session=session, user_id=user_id, doc_id=body.doc_id
    ):  # source of truth = DB
        raise HTTPException(403, "no access to this document")
    return {
        "ticket": await tickets.issue(user_id, body.doc_id),
        "expires_in": config.TICKET_TTL_SECONDS,
    }
