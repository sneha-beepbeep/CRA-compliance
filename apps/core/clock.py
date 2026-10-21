"""Server clock (NFR-4: the server clock is authoritative). Patched in tests."""
from datetime import datetime, timezone


def now() -> datetime:
    return datetime.now(timezone.utc)


def now_minute() -> datetime:
    return now().replace(second=0, microsecond=0)
