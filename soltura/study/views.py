from dataclasses import dataclass
from urllib.parse import quote

from soltura.learner.models import StudyStep
from soltura.study.service import STEPS

SESSION_HREF = "/study"
SUMMARY_HREF = "/study/summary"

STEP_CONTENT: dict[StudyStep, tuple[str, str, str]] = {
    StudyStep.WARMUP: ("Розминка", "Короткі вправи на слова, які пора повторити", "/warmup"),
    StudyStep.READING: (
        "Читання",
        "Текст за темою сесії; тапніть слово, щоб побачити переклад і зберегти",
        "/reading?topic={topic}",
    ),
    StudyStep.GRAMMAR: ("Граматика", "Правило або вправи, які пора повторити", "/grammar"),
    StudyStep.WRITING: (
        "Письмо",
        "Кілька речень іспанською за темою сесії",
        "/journal?topic={topic}",
    ),
}


@dataclass(frozen=True)
class StepView:
    step: str
    label: str
    purpose: str
    href: str
    state: str


@dataclass(frozen=True)
class StudyView:
    topic: str
    steps: list[StepView]
    current: StepView


def landing_href(step: StudyStep, topic: str) -> str:
    # Where a step is carried out; a finished session has the summary of the sitting.
    if step not in STEP_CONTENT:
        return SUMMARY_HREF
    return STEP_CONTENT[step][2].format(topic=quote(topic, safe=""))


def study_view(topic: str, current: StudyStep) -> StudyView:
    order = STEPS.index(current)
    steps = [
        StepView(
            step=step.value,
            label=STEP_CONTENT[step][0],
            purpose=STEP_CONTENT[step][1],
            href=landing_href(step, topic),
            state="done" if index < order else "current" if index == order else "upcoming",
        )
        for index, step in enumerate(STEPS)
        if step in STEP_CONTENT
    ]
    return StudyView(topic=topic, steps=steps, current=steps[order])
