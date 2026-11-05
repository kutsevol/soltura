import pytest
from fastapi import HTTPException
from pydantic import TypeAdapter

from soltura.web import MAX_DURATION_MS, answer_duration_ms, parse_state

NUMBERS = TypeAdapter(list[int])


def test_a_good_state_is_parsed() -> None:
    assert parse_state(NUMBERS, "[1, 2]", "Bad state") == [1, 2]


def test_a_bad_state_is_a_bad_request_with_the_pages_message() -> None:
    with pytest.raises(HTTPException) as error:
        parse_state(NUMBERS, '["x"]', "Bad warm-up state")

    assert (error.value.status_code, error.value.detail) == (400, "Bad warm-up state")


@pytest.mark.parametrize(
    ("started_at", "now", "expected"),
    [
        (1_000, 3_500, 2_500),
        (5_000, 1_000, 0),
        (0, MAX_DURATION_MS + 1, MAX_DURATION_MS),
    ],
    ids=["elapsed", "clock-went-back", "left-open"],
)
def test_the_answer_time_is_clamped_between_zero_and_ten_minutes(
    started_at: int, now: int, expected: int
) -> None:
    assert answer_duration_ms(started_at, now) == expected
