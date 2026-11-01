from dataclasses import replace

import fsrs
import pytest

from soltura.srs.service import get_scheduler


@pytest.fixture
def scheduler() -> fsrs.Scheduler:
    # The production scheduler with fuzzing off: the same review always lands on the same due date.
    return replace(get_scheduler(), enable_fuzzing=False)
