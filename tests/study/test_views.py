from urllib.parse import quote

from soltura.learner.models import StudyStep
from soltura.study.views import landing_href, study_view


def test_the_steps_before_the_current_one_are_done_and_the_rest_upcoming() -> None:
    view = study_view("Покупки", StudyStep.GRAMMAR)

    assert [(step.label, step.state) for step in view.steps] == [
        ("Розминка", "done"),
        ("Читання", "done"),
        ("Граматика", "current"),
        ("Письмо", "upcoming"),
    ]
    assert view.current.href == "/grammar"


def test_reading_and_writing_open_on_the_topic_of_the_session() -> None:
    view = study_view("Сусіди й бар", StudyStep.WARMUP)

    hrefs = {step.label: step.href for step in view.steps}
    topic = quote("Сусіди й бар", safe="")
    assert hrefs["Читання"] == f"/reading?topic={topic}"
    assert hrefs["Письмо"] == f"/journal?topic={topic}"
    assert "й" not in hrefs["Читання"]


def test_a_finished_session_leads_to_its_summary() -> None:
    assert landing_href(StudyStep.DONE, "Покупки") == "/study/summary"
