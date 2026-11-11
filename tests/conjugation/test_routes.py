import re
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.config import settings
from soltura.learner.models import (
    KnowledgeType,
    Learner,
    Lexeme,
    MemoryCard,
    ReviewLog,
    ReviewSource,
    UnitKind,
)
from soltura.srs.service import schedule_units
from soltura.use_cases.conjugation import answer_item

SER_PRESENT = ["soy", "eres", "es", "somos", "sois", "son"]


def _hidden(html: str, name: str) -> str:
    match = re.search(rf'name="{name}" value="([^"]*)"', html)
    assert match, f"no hidden field {name}"
    return match.group(1).replace("&#34;", '"').replace("&quot;", '"').replace("&amp;", "&")


async def _answer(client: AsyncClient, page: str, answer: str, give_up: bool = False) -> str:
    data = {
        "card_id": _hidden(page, "card_id"),
        "queue": _hidden(page, "queue"),
        "started_at": _hidden(page, "started_at"),
        "answer": answer,
    }
    if give_up:
        data["give_up"] = "1"
    response = await client.post("/conjugation/answer", data=data)
    assert response.status_code == 200
    return response.text


async def _next(client: AsyncClient, result: str) -> str:
    response = await client.post("/conjugation/next", data={"queue": _hidden(result, "queue")})
    assert response.status_code == 200
    return response.text


async def test_a_session_goes_through_every_card_and_ends_on_the_done_screen(
    learner_client: AsyncClient, session: AsyncSession, verb_lexemes: list[Lexeme]
) -> None:
    page = (await learner_client.get("/conjugation")).text
    assert "<strong>ser</strong>" in page and "yo …" in page and "Ще карток: 5" in page

    for index, form in enumerate(SER_PRESENT):
        result = await _answer(learner_client, page, form)
        assert "Правильно" in result
        page = await _next(learner_client, result)
        if index < len(SER_PRESENT) - 1:
            assert f"Ще карток: {len(SER_PRESENT) - index - 2}" in page

    assert "Сесію завершено" in page
    logs = (await session.execute(select(ReviewLog))).scalars().all()
    assert [log.answer for log in logs] == SER_PRESENT
    assert {log.source for log in logs} == {ReviewSource.CONJUGATION}


async def test_a_wrong_answer_shows_the_verdict_and_the_right_form(
    learner_client: AsyncClient, verb_lexemes: list[Lexeme]
) -> None:
    page = (await learner_client.get("/conjugation")).text

    result = await _answer(learner_client, page, "eres")

    assert "Ще раз" in result
    assert "Ваша відповідь: eres" in result
    assert "Очікувалось: <strong>soy</strong>" in result
    assert "tú …" in await _next(learner_client, result)


async def test_giving_up_shows_the_right_form(
    learner_client: AsyncClient, verb_lexemes: list[Lexeme]
) -> None:
    page = (await learner_client.get("/conjugation")).text

    result = await _answer(learner_client, page, "soy", give_up=True)

    assert "Ще раз" in result
    assert "Очікувалось: <strong>soy</strong>" in result


async def test_a_learner_with_no_verbs_to_practise_sees_the_done_screen(
    learner_client: AsyncClient,
) -> None:
    page = await learner_client.get("/conjugation")

    assert page.status_code == 200
    assert "Сесію завершено" in page.text


async def test_a_broken_session_state_is_refused(learner_client: AsyncClient) -> None:
    response = await learner_client.post("/conjugation/next", data={"queue": "not json"})

    assert response.status_code == 400


async def test_the_page_of_a_verb_lists_every_tense_and_person(learner_client: AsyncClient) -> None:
    page = await learner_client.get("/conjugation/verbs/ser")

    assert page.status_code == 200
    assert page.text.count("<tr>") == 24
    assert "<td>soy</td>" in page.text and "<td>fueron</td>" in page.text
    assert "presente" in page.text and "futuro" in page.text


@pytest.mark.parametrize("verb", ["zzzar", "llover", "resultar", "dar%20%C3%A9l", "x"])
async def test_the_page_of_a_verb_that_cannot_be_conjugated_is_a_404(
    learner_client: AsyncClient, verb: str
) -> None:
    response = await learner_client.get(f"/conjugation/verbs/{verb}")

    assert response.status_code == 404


async def test_the_endings_page_shows_the_three_conjugations_side_by_side(
    learner_client: AsyncClient,
) -> None:
    page = await learner_client.get("/conjugation/endings")

    assert page.status_code == 200
    for header in ("-ar", "-er", "-ir"):
        assert f'<th scope="col">{header}</th>' in page.text
    assert "<td>-amos</td><td>-emos</td><td>-imos</td>" in page.text


async def test_an_answer_links_to_the_table_of_its_verb(
    learner_client: AsyncClient, session: AsyncSession, verb_lexemes: list[Lexeme]
) -> None:
    page = (await learner_client.get("/conjugation")).text

    result = await _answer(learner_client, page, "x", give_up=True)

    assert re.search(r'href="/conjugation/verbs/[a-zñáéíóú]+"', result)


@pytest.mark.parametrize("path", ["/conjugation/verbs/ser", "/conjugation/endings"])
async def test_the_reference_pages_need_a_learner(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    monkeypatch.setattr(settings.auth, "dev_telegram_user_id", None)

    assert (await client.get(path)).status_code == 401


@pytest.mark.parametrize("verb", ["HABLAR", "o%C3%ADr"])
async def test_a_verb_in_capitals_or_with_an_accent_has_its_page(
    learner_client: AsyncClient, verb: str
) -> None:
    assert (await learner_client.get(f"/conjugation/verbs/{verb}")).status_code == 200


@pytest.mark.parametrize(("verb", "form"), [("haber", "habéis"), ("pasar", "pasábamos")])
async def test_haber_and_pasar_have_their_tables(
    learner_client: AsyncClient, verb: str, form: str
) -> None:
    page = await learner_client.get(f"/conjugation/verbs/{verb}")

    assert page.status_code == 200
    assert f"<td>{form}</td>" in page.text


async def test_after_the_daily_cap_the_screen_says_there_are_enough_new_forms(
    learner_client: AsyncClient, verb_lexemes: list[Lexeme], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.conjugation, "new_sets_per_day", 1)
    page = (await learner_client.get("/conjugation")).text
    for form in SER_PRESENT:
        page = await _next(learner_client, await _answer(learner_client, page, form))

    again = (await learner_client.get("/conjugation")).text

    assert "На сьогодні нових форм досить" in again
    assert "Сесію завершено" not in again


async def test_the_last_card_of_a_capped_day_ends_on_the_cap_message(
    learner_client: AsyncClient, verb_lexemes: list[Lexeme], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.conjugation, "new_sets_per_day", 1)
    page = (await learner_client.get("/conjugation")).text
    for form in SER_PRESENT:
        page = await _next(learner_client, await _answer(learner_client, page, form))

    assert "На сьогодні нових форм досить" in page
    assert "Сесію завершено" not in page


async def test_the_last_card_before_the_cap_ends_on_the_plain_message(
    learner_client: AsyncClient, verb_lexemes: list[Lexeme]
) -> None:
    page = (await learner_client.get("/conjugation")).text
    for form in SER_PRESENT:
        page = await _next(learner_client, await _answer(learner_client, page, form))

    assert "Сесію завершено" in page


async def _answer_all(
    session: AsyncSession, learner: Learner, key: str, answers: list[str]
) -> None:
    assert learner.id is not None
    now = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)
    await schedule_units(
        session, learner.id, UnitKind.CONJUGATION, [key], KnowledgeType.RECALL, now
    )
    card = await session.scalar(select(MemoryCard).where(col(MemoryCard.unit_key) == key))
    assert card is not None and card.id is not None
    for answer in answers:
        await answer_item(session, learner.id, card.id, answer, 1000, now)


async def test_the_progress_page_of_a_learner_without_answers_links_to_the_trainer(
    learner_client: AsyncClient,
) -> None:
    page = await learner_client.get("/conjugation/progress")

    assert page.status_code == 200
    assert "Ще немає відповідей з відмінювання." in page.text
    assert 'href="/conjugation" role="button"' in page.text
    assert "%" not in page.text


async def test_a_tense_with_few_answers_shows_the_count_and_no_percentage(
    learner_client: AsyncClient, session: AsyncSession, learner: Learner
) -> None:
    await _answer_all(session, learner, "ser|present|yo", ["soy"] * 3)

    page = await learner_client.get("/conjugation/progress")

    assert "Відповідей: 3" in page.text
    assert "Ще мало відповідей для відсотка" in page.text
    assert "правильних" not in page.text


async def test_an_accent_slip_lowers_the_percentage_and_a_correct_answer_raises_it(
    learner_client: AsyncClient, session: AsyncSession, learner: Learner
) -> None:
    await _answer_all(session, learner, "tener|present|vosotros", ["tenéis"] * 10)
    full = await learner_client.get("/conjugation/progress")
    await _answer_all(session, learner, "tener|present|vosotros", ["teneis"])
    slipped = await learner_client.get("/conjugation/progress")
    await _answer_all(session, learner, "tener|present|vosotros", ["tenéis"])
    recovered = await learner_client.get("/conjugation/progress")

    assert "Відповідей: 10, правильних: 100%" in full.text
    assert "Відповідей: 11, правильних: 91%" in slipped.text
    assert "Відповідей: 12, правильних: 92%" in recovered.text


async def test_the_trainer_page_links_to_the_progress_page(learner_client: AsyncClient) -> None:
    page = await learner_client.get("/conjugation")

    assert 'href="/conjugation/progress"' in page.text
