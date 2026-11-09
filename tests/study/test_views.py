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


def test_a_finished_session_leads_to_the_session_page() -> None:
    assert landing_href(StudyStep.DONE) == "/study"
