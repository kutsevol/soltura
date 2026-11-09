from httpx import AsyncClient

from soltura.llm.client import LLMUnavailableError
from soltura.writing.prompts import PROMPTS
from soltura.writing.service import Correction, FoundError
from tests.fakes import FakeLLM

TEXT = "Yo soy cansado porque trabajo mucho."
FIXED = "Estoy cansado porque trabajo mucho."
CORRECTION = Correction(
    corrected_text=FIXED,
    errors=[
        FoundError(
            original="Yo soy", corrected="Estoy", category="ser_estar", note="Стан — це estar."
        )
    ],
)


async def test_the_journal_page_offers_the_tasks_and_a_free_topic(
    learner_client: AsyncClient,
) -> None:
    page = await learner_client.get("/journal")

    assert page.status_code == 200
    assert "Вільна тема" in page.text
    assert all(prompt in page.text for prompt in PROMPTS)
    assert 'hx-target="#result"' in page.text
    assert "Попередні тексти" not in page.text


async def test_a_text_with_a_mistake_shows_the_diff_and_a_note_per_error(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(CORRECTION)

    response = await learner_client.post("/journal", data={"text": TEXT, "prompt": PROMPTS[0]})

    assert response.status_code == 200
    assert "<del>Yo soy</del><ins>Estoy</ins> cansado porque trabajo mucho." in response.text
    assert "Знайдено помилок: 1" in response.text
    assert "Стан — це estar." in response.text
    assert "Граматика" in response.text


async def test_a_text_without_errors_says_so(learner_client: AsyncClient, llm: FakeLLM) -> None:
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    response = await learner_client.post("/journal", data={"text": TEXT})

    assert "Помилок не знайдено" in response.text
    assert "<del>" not in response.text


async def test_a_text_that_is_too_short_is_refused_and_the_model_is_not_called(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    response = await learner_client.post("/journal", data={"text": "Hola."})

    assert response.status_code == 422
    assert "від 20 символів" in response.text
    assert llm.prompts == []


async def test_a_text_that_is_too_long_is_refused(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    response = await learner_client.post("/journal", data={"text": "a" * 1_001})

    assert response.status_code == 422
    assert "не більше 1000 символів" in response.text
    assert llm.prompts == []


async def test_when_the_model_is_unavailable_the_page_says_so_and_nothing_is_saved(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.fail(Correction, LLMUnavailableError("down"))

    response = await learner_client.post("/journal", data={"text": TEXT})
    page = await learner_client.get("/journal")

    assert response.status_code == 503
    assert "Зараз не вдається отримати відповідь від моделі" in response.text
    assert "Попередні тексти" not in page.text


async def test_a_submitted_text_appears_among_the_past_texts(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(CORRECTION)
    await learner_client.post("/journal", data={"text": TEXT, "prompt": PROMPTS[1]})

    page = await learner_client.get("/journal")

    assert "Попередні тексти" in page.text
    assert PROMPTS[1] in page.text.split("Попередні тексти")[1]
    assert "<del>Yo soy</del><ins>Estoy</ins>" in page.text


async def test_markup_in_the_text_and_in_the_model_note_is_escaped(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    text = "Yo <script>alert(1)</script> soy cansado hoy."
    llm.answer(
        Correction(
            corrected_text=text,
            errors=[
                FoundError(
                    original="soy cansado",
                    corrected="estoy cansado",
                    category="other",
                    note="<script>alert(2)</script>",
                )
            ],
        )
    )

    response = await learner_client.post("/journal", data={"text": text})

    assert "<script>" not in response.text
    assert "&lt;script&gt;alert(2)&lt;/script&gt;" in response.text


async def test_an_error_in_a_grammar_unit_links_to_its_lesson(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(CORRECTION)

    response = await learner_client.post("/journal", data={"text": TEXT})

    assert 'href="/grammar/units/ser_estar"' in response.text


async def test_an_error_outside_the_grammar_units_has_no_lesson_link(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(
        Correction(
            corrected_text=FIXED,
            errors=[
                FoundError(original="Yo soy", corrected="Estoy", category="spelling", note="n")
            ],
        )
    )

    response = await learner_client.post("/journal", data={"text": TEXT})

    assert "/grammar/units/" not in response.text


async def test_the_errors_page_counts_per_category_and_suggests_a_unit_after_three(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    for _ in range(3):
        llm.answer(CORRECTION)
        await learner_client.post("/journal", data={"text": TEXT})

    page = await learner_client.get("/journal/errors")

    assert page.status_code == 200
    assert "· 3" in page.text
    assert "<del>Yo soy</del> → <ins>Estoy</ins>" in page.text
    assert "Варто перечитати урок" in page.text
    assert 'href="/grammar/units/ser_estar"' in page.text


async def test_the_errors_page_does_not_suggest_a_unit_after_two_errors(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    for _ in range(2):
        llm.answer(CORRECTION)
        await learner_client.post("/journal", data={"text": TEXT})

    page = await learner_client.get("/journal/errors")

    assert "· 2" in page.text
    assert "Варто перечитати урок" not in page.text


async def test_the_errors_page_without_entries_points_to_the_journal(
    learner_client: AsyncClient,
) -> None:
    page = await learner_client.get("/journal/errors")

    assert page.status_code == 200
    assert 'href="/journal"' in page.text
    assert "Помилок поки немає" in page.text
