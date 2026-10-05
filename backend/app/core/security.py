from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from pwdlib import PasswordHash
from datetime import timedelta

from app.utils import _utcnow
import app.config as config

# for deprecated, google this topic.
# deprecated is for later use. not req now though
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password_hash = PasswordHash.recommended()


#  ── password hashing and verification ─────────────────────────────────────────────────────────────────


def hash_password(password: str):
    # return pwd_context.hash(password)
    return password_hash.hash(password)


def verify_password(password: str, hash: str) -> bool:
    # return pwd_context.verify(password, _password_hash)
    return password_hash.verify(password, hash)


#  ── JWT tokens encoding and decoding ─────────────────────────────────────────────────────────────────


def create_access_token(user_id: str, expires_delta: timedelta):
    now = _utcnow()
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(payload, config.settings.JWT_SECRET, config.jwt_algorithm)
    return token


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, config.settings.JWT_SECRET, config.jwt_algorithm)
        return payload

    except ExpiredSignatureError:
        print("Token has expired")
        raise
    except JWTError:
        print("Invalid token")
        raise
