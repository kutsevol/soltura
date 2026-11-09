from soltura.learner.models import StudyStep
from soltura.study.service import next_step


def test_the_steps_follow_each_other_and_stop_at_done() -> None:
    walked = [StudyStep.WARMUP]
    for _ in range(5):
        walked.append(next_step(walked[-1]))

    assert walked == [
        StudyStep.WARMUP,
        StudyStep.READING,
        StudyStep.GRAMMAR,
        StudyStep.WRITING,
        StudyStep.DONE,
        StudyStep.DONE,
    ]
