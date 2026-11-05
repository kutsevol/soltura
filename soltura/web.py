import time

from fastapi import HTTPException, status
from pydantic import TypeAdapter, ValidationError

# An answer that took longer was left open in a tab, not thought about.
MAX_DURATION_MS = 10 * 60 * 1000


def now_ms() -> int:
    return time.time_ns() // 1_000_000


def answer_duration_ms(started_at: int, now: int) -> int:
    return min(max(now - started_at, 0), MAX_DURATION_MS)


def parse_state[T](adapter: TypeAdapter[T], raw: str, detail: str) -> T:
    # The page carries its state in hidden fields, so a bad one is a bad request, not a crash.
    try:
        return adapter.validate_json(raw)
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from error
