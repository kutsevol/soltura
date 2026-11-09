from datetime import timedelta

from soltura.learner.models import StudyStep

STEPS = (
    StudyStep.WARMUP,
    StudyStep.READING,
    StudyStep.GRAMMAR,
    StudyStep.WRITING,
    StudyStep.DONE,
)
# A session left open overnight is a forgotten tab, not a sitting in progress.
OPEN_FOR = timedelta(hours=12)


def next_step(step: StudyStep) -> StudyStep:
    return STEPS[min(STEPS.index(step) + 1, len(STEPS) - 1)]
