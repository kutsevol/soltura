from dataclasses import dataclass

from soltura.learner.models import StudyStep
from soltura.study.service import STEPS

SESSION_HREF = "/study"

STEP_CONTENT: dict[StudyStep, tuple[str, str, str]] = {
    StudyStep.WARMUP: ("Розминка", "Короткі вправи на слова, які пора повторити", "/warmup"),
    StudyStep.READING: (
        "Читання",
        "Текст за темою сесії; тапніть слово, щоб побачити переклад і зберегти",
        "/reading",
    ),
    StudyStep.GRAMMAR: ("Граматика", "Правило або вправи, які пора повторити", "/grammar"),
    StudyStep.WRITING: ("Письмо", "Кілька речень іспанською за темою сесії", "/journal"),
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


def landing_href(step: StudyStep) -> str:
    # Where a step is carried out; a finished session has no screen but the session page.
    return STEP_CONTENT[step][2] if step in STEP_CONTENT else SESSION_HREF


def study_view(topic: str, current: StudyStep) -> StudyView:
    order = STEPS.index(current)
    steps = [
        StepView(
            step=step.value,
            label=STEP_CONTENT[step][0],
            purpose=STEP_CONTENT[step][1],
            href=STEP_CONTENT[step][2],
            state="done" if index < order else "current" if index == order else "upcoming",
        )
        for index, step in enumerate(STEPS)
        if step in STEP_CONTENT
    ]
    return StudyView(topic=topic, steps=steps, current=steps[order])
