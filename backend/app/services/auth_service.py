import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
import secrets
from typing import TYPE_CHECKING

import app.config as config
from app.utils import _utcnow, _aware, _hash
from app.repositories.user_repo import UserRepository
from app.repositories.refresh_repo import RefreshRepository
from app.services.document_service import DocumentService
from app.core.security import hash_password, create_access_token, verify_password
from app.models.models import User
from app.schemas.schemas import AuthResponse, UserOut, UserLogin, UserCreate

if TYPE_CHECKING:
    from app.models.models import RefreshToken


class AuthService:
    def __init__(self):
        self.repo = UserRepository()
        self.refresh_repo = RefreshRepository()
        self.doc_service = DocumentService()

    async def _email_already_registered(
        self, session: AsyncSession, email: str
    ) -> bool:
        # returns true if email already registered, else false
        return await self.repo.get_by_email(session=session, email=email) is not None

    async def register(
        self, session: AsyncSession, request: UserCreate, response: Response
    ) -> dict:
        # extract info
        name = request.name
        email = request.email
        password = request.password

        # check if email already registered
        email_already_registered = await self._email_already_registered(session, email)

        if email_already_registered:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )

        # hash the password
        password_hash = hash_password(password)
        # create user
        user: User = await self.repo.create(
            session=session, email=email, name=name, password_hash=password_hash
        )

        # add the user to docCollaborator table as an `editor` to the only document `shared_doc`
        self.doc_service.give_user_access(
            session=session, doc_id="shared_doc", user_id=user.id
        )
        return {"success": "true", "message": "user registered successfully"}

        # return await self.start_session(
        #     session=session, response=response, user_id=str(user.id)
        # )

    # ───────── login ────────────────────────────────────────────────────────────

    async def login(
        self, session: AsyncSession, request: UserLogin, response: Response
    ) -> dict:
        email = request.email
        password = request.password

        # get user by email
        user: User | None = await self.repo.get_by_email(session=session, email=email)

        if user is None:
            return self._unauthorized("invalid credentials")

        # verify password
        match = verify_password(password, user.password_hash)

        if not match:
            return self._unauthorized("invalid credentials")

        access_payload = await self.start_session(
            session=session, response=response, user_id=str(user.id)
        )
        return access_payload | {"name": user.name}

    async def start_session(
        self, session: AsyncSession, response: Response, user_id: str
    ) -> dict:
        # del expired tokens (opportunistic gc)garbage collection
        # await self.del_expired_refresh_tokens(session=session)

        raw_token = secrets.token_urlsafe(48)
        self.refresh_repo.create_row(
            session=session, user_id=user_id, family_id=uuid.uuid4().hex, raw=raw_token
        )
        # store the refresh token as cookie
        self._set_cookie(response=response, raw=raw_token)

        return self._access_payload(user_id)

    # ───────── refresh ────────────────────────────────────────────────────────────

    async def refresh(
        self,
        session: AsyncSession,
        request: Request,
        response: Response,
    ):
        # check if the origin is allowed
        self._require_allowed_origin(request.headers)

        # get the raw refresh token from the reuest cookie
        raw = request.cookies.get(config.COOKIE_NAME)
        if not raw:
            return self._unauthorized("no refresh token")

        now = _utcnow()

        row = await self.refresh_repo.get_row(session=session, token_hash=_hash(raw))
        if row is None or _aware(row.expires_at) < now:
            return self._unauthorized("invalid or expired refresh token")

        if row.used_at is not None:
            if now - _aware(row.used_at) <= config.REUSE_GRACE:
                # Benign race (e.g. two tabs). The winner already put the new cookie in the browser,
                # so just hand out an access token and leave the cookie alone.
                return self._access_payload(row.user_id)

            # An already-rotated token came back later: someone replayed a stolen copy.
            # Kill the entire family -> the real user and the attacker both have to log in again.
            await self.refresh_repo.delete_family(
                session=session, family_id=row.family_id
            )
            return self._unauthorized("refresh token reuse detected")

        row.used_at = now

        # CREATE NEW REFRESH TOKEN
        new_raw = secrets.token_urlsafe(48)
        self.refresh_repo.create_row(
            session=session, user_id=row.user_id, raw=new_raw, family_id=row.family_id
        )

        # # dont need to del the existing cookie
        # # setcookie overwrites the existing cookie if the name and path match
        # self.del_cookie(
        #     response=response,
        #     cookie_path=config.COOKIE_PATH,
        #     cookie_name=config.COOKIE_NAME,
        # )
        # store the refresh token as cookie
        self._set_cookie(response=response, raw=new_raw)

        return self._access_payload(user_id=str(row.user_id))

    # ───────── logout ────────────────────────────────────────────────────────────
    async def logout(self, session: AsyncSession, request: Request):
        self._require_allowed_origin(request.headers)
        raw = request.cookies.get("refresh_token")
        if raw:
            row = await self.refresh_repo.get_row(
                session=session, token_hash=_hash(raw), for_update=False
            )

            if row:
                await self.refresh_repo.delete_family(
                    session=session, family_id=row.family_id
                )

        resp = JSONResponse({"ok": True})
        # resp.delete_cookie(config.COOKIE_NAME, path=config.COOKIE_PATH)
        self.del_cookie(
            response=resp,
            cookie_path=config.COOKIE_PATH,
            cookie_name=config.COOKIE_NAME,
        )
        return resp

    # ───────── helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _require_allowed_origin(headers: dict) -> None:
        # Extra CSRF defence for the cookie-authenticated endpoints.
        if headers.get("origin", "").rstrip("/") not in config.settings.ALLOWED_ORIGINS:
            raise HTTPException(403, "origin not allowed")

    @staticmethod
    def _unauthorized(detail: str) -> JSONResponse:
        resp = JSONResponse({"detail": detail}, status_code=401)
        resp.delete_cookie(config.COOKIE_NAME, path=config.COOKIE_PATH)
        return resp

    @staticmethod
    def _access_payload(user_id: str) -> dict:
        token = create_access_token(user_id=user_id, expires_delta=config.ACCESS_TTL)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": int(config.ACCESS_TTL.total_seconds()),
        }

    async def del_expired_refresh_tokens(self, session: AsyncSession) -> None:
        await self.refresh_repo.del_expired_tokens(session=session, _after=_utcnow())

    @staticmethod
    def del_cookie(response: Response, cookie_name: str, cookie_path: str) -> None:
        response.delete_cookie(key=cookie_name, path=cookie_path)

    @staticmethod
    def _set_cookie(response: Response, raw: str) -> None:
        response.set_cookie(
            key=config.COOKIE_NAME,
            value=raw,
            max_age=int(config.REFRESH_TTL.total_seconds()),
            httponly=True,  # JS cant read; XSS cant steal
            secure=config.COOKIE_SECURE,
            samesite="lax",  # CSRF
            path=config.COOKIE_PATH,
        )
