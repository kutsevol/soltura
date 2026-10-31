import fsrs
import pytest


@pytest.fixture
def scheduler() -> fsrs.Scheduler:
    # Fuzzing randomizes intervals; off, the same review always lands on the same due date.
    return fsrs.Scheduler(enable_fuzzing=False)
