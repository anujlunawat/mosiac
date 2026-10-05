import hashlib
from datetime import datetime, timezone


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# timezone aware
def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
