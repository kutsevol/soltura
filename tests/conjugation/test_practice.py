import random
import re

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from soltura.conjugation.forms import Person, Tense, conjugate
from soltura.conjugation.routes import MAX_PRACTICE_QUEUE
from soltura.conjugation.service import (
    CONJUGATION_RATING,
    PracticeItem,
    check_practice,
    practice_queue,
)
from soltura.learner.models import LearnerLexeme, MemoryCard, ReviewLog
from soltura.practice.checking import SpanishCheck
from soltura.use_cases.conjugation import InvalidPractice, PracticeProblem, start_practice


def test_every_person_of_each_chosen_tense_is_asked_once_in_a_mixed_order() -> None:
    queue = practice_queue("comer", [Tense.PRESENT, Tense.PRETERITE], random.Random(1))

    assert queue is not None
    assert len(queue) == 12
    assert {(item.tense, item.person) for item in queue} == {
        (tense, person) for tense in (Tense.PRESENT, Tense.PRETERITE) for person in Person
    }
    assert all(item.verb == "comer" for item in queue)
    in_order = [(item.tense, item.person) for item in queue]
    assert in_order != sorted(
        in_order, key=lambda pair: (list(Tense).index(pair[0]), list(Person).index(pair[1]))
    )


def test_two_seeds_give_two_orders_and_one_seed_gives_one() -> None:
    first = practice_queue("comer", list(Tense), random.Random(1))
    again = practice_queue("comer", list(Tense), random.Random(1))
    other = practice_queue("comer", list(Tense), random.Random(2))

    assert first == again != other


def test_a_tense_chosen_twice_is_asked_once_and_the_verb_is_cleaned() -> None:
    queue = practice_queue("  Comer ", [Tense.PRESENT, Tense.PRESENT], random.Random(1))

    assert queue is not None and len(queue) == len(Person)
    assert {item.verb for item in queue} == {"comer"}


@pytest.mark.parametrize("verb", ["", "x", "zzzar", "llover", "lavarse", "ser;drop", "../etc"])
def test_a_word_that_cannot_be_conjugated_gives_no_queue(verb: str) -> None:
    assert practice_queue(verb, [Tense.PRESENT], random.Random(1)) is None


@pytest.mark.parametrize(
    ("answer", "check"),
    [
        ("como", SpanishCheck.EXACT),
        ("Como ", SpanishCheck.EXACT),
        ("comí", SpanishCheck.TYPO),
        ("bebo", SpanishCheck.WRONG),
        ("", SpanishCheck.WRONG),
    ],
)
def test_an_answer_is_judged_as_in_the_scheduled_trainer(answer: str, check: SpanishCheck) -> None:
    result = check_practice(PracticeItem("comer", Tense.PRESENT, Person.YO), answer)

    assert (result.check, result.rating) == (check, CONJUGATION_RATING[check])
    assert (result.expected, result.verb, result.tense) == ("como", "comer", Tense.PRESENT)


def test_a_missing_accent_is_a_slip_and_the_expected_form_comes_back() -> None:
    item = PracticeItem("comer", Tense.PRETERITE, Person.EL)

    result = check_practice(item, "comio")

    assert result.check == SpanishCheck.ACCENT_SLIP and result.expected == "comió"


@pytest.mark.parametrize("verb", ["", "ser;drop", "zzzar", "llover"])
def test_an_item_that_names_no_verb_is_an_error(verb: str) -> None:
    with pytest.raises(ValueError, match="cannot be conjugated"):
        check_practice(PracticeItem(verb, Tense.PRESENT, Person.YO), "como")


def test_no_tense_and_an_unknown_verb_are_named() -> None:
    with pytest.raises(InvalidPractice) as no_tense:
        start_practice("comer", [])
    with pytest.raises(InvalidPractice) as unknown:
        start_practice("zzzar", [Tense.PRESENT])

    assert no_tense.value.problem == PracticeProblem.NO_TENSE
    assert unknown.value.problem == PracticeProblem.UNKNOWN_VERB


def _hidden(html: str, name: str) -> str:
    match = re.search(rf'name="{name}" value="([^"]*)"', html)
    assert match, f"no hidden field {name}"
    return match.group(1).replace("&#34;", '"').replace("&quot;", '"').replace("&amp;", "&")


async def _start(
    client: AsyncClient, verb: str = "comer", tenses: tuple[str, ...] = ("present",)
) -> str:
    response = await client.post(
        "/conjugation/practice/start", data={"verb": verb, "tense": tenses}
    )
    assert response.status_code == 200
    return response.text


def _answer_data(card: str, answer: str) -> dict[str, str]:
    return {
        "verb": _hidden(card, "verb"),
        "tense": _hidden(card, "tense"),
        "person": _hidden(card, "person"),
        "queue": _hidden(card, "queue"),
        "answer": answer,
    }


async def test_the_page_ticks_only_the_present_and_fills_in_a_verb_from_the_address(
    learner_client: AsyncClient,
) -> None:
    page = await learner_client.get("/conjugation/practice", params={"verb": '"><b>comer'})

    assert page.status_code == 200
    assert page.text.count(" checked") == 1
    assert page.text.count('name="tense"') == len(Tense)
    assert "<b>" not in page.text and "&#34;&gt;&lt;b&gt;comer" in page.text


async def test_a_verb_and_two_tenses_start_twelve_cards(learner_client: AsyncClient) -> None:
    card = await _start(learner_client, tenses=("present", "preterite"))

    assert "Ще форм: 11" in card and "<strong>comer</strong>" in card


async def test_a_session_goes_through_every_form_with_the_trainers_verdicts_and_ends(
    learner_client: AsyncClient,
) -> None:
    card = await _start(learner_client)
    seen = []
    for _ in range(len(Person)):
        item = PracticeItem(
            _hidden(card, "verb"),
            Tense(_hidden(card, "tense")),
            Person(_hidden(card, "person")),
        )
        seen.append(item.person)
        form = conjugate(item.verb, item.tense, item.person)
        assert form is not None
        result = await learner_client.post(
            "/conjugation/practice/answer", data=_answer_data(card, form)
        )
        assert result.status_code == 200 and "Правильно" in result.text
        assert 'hx-post="/conjugation/practice/next"' in result.text
        next_card = await learner_client.post(
            "/conjugation/practice/next", data={"queue": _hidden(result.text, "queue")}
        )
        card = next_card.text

    assert sorted(seen) == sorted(Person)
    assert "усі форми пройдено" in card


async def test_a_wrong_answer_shows_the_right_form_and_the_notes_of_the_verb(
    learner_client: AsyncClient,
) -> None:
    card = await _start(learner_client, "tener", ("preterite",))
    data = _answer_data(card, "")
    data["verb"], data["tense"], data["person"] = "tener", "preterite", "yo"

    result = await learner_client.post("/conjugation/practice/answer", data=data)

    assert "Очікувалось: <strong>tuve</strong>" in result.text
    assert "«Сильний» претерит" in result.text


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({"verb": "zzzar", "tense": ["present"]}, "Не вдалося відмінювати"),
        ({"verb": "llover", "tense": ["present"]}, "Не вдалося відмінювати"),
        ({"verb": "comer", "tense": []}, "Оберіть хоча б один час"),
        ({"verb": "comer", "tense": ["nonsense"]}, "Оберіть хоча б один час"),
        ({"verb": " ", "tense": ["present"]}, "Не вдалося відмінювати"),
    ],
    ids=["unknown", "weather", "no tense", "bad tense", "blank"],
)
async def test_a_verb_that_cannot_be_conjugated_or_no_tense_is_refused_with_a_message(
    learner_client: AsyncClient, data: dict[str, object], message: str
) -> None:
    response = await learner_client.post("/conjugation/practice/start", data=data)

    assert response.status_code == 422
    assert message in response.text
    assert response.headers["content-type"].startswith("text/html")


async def test_a_tampered_form_is_refused_without_checking_an_answer(
    learner_client: AsyncClient,
) -> None:
    card = await _start(learner_client)
    good = _answer_data(card, "como")
    too_long = (
        "["
        + ",".join(['{"verb":"comer","tense":"present","person":"yo"}'] * MAX_PRACTICE_QUEUE)
        + "]"
    )

    for bad in (
        {**good, "queue": "not json"},
        {**good, "verb": "ser;drop"},
        {**good, "tense": "pluperfect"},
        {**good, "person": "usted"},
        {**good, "queue": too_long},
    ):
        response = await learner_client.post("/conjugation/practice/answer", data=bad)
        assert response.status_code == 400
    assert (
        await learner_client.post("/conjugation/practice/next", data={"queue": "not json"})
    ).status_code == 400


async def test_practising_writes_nothing(
    learner_client: AsyncClient, session: AsyncSession
) -> None:
    card = await _start(learner_client, tenses=("present", "future"))
    await learner_client.post("/conjugation/practice/answer", data=_answer_data(card, "como"))
    await learner_client.post("/conjugation/practice/answer", data=_answer_data(card, ""))

    for table in (MemoryCard, ReviewLog, LearnerLexeme):
        assert (await session.execute(select(table))).scalars().all() == []


async def test_the_verb_page_and_the_trainer_link_to_the_drill(learner_client: AsyncClient) -> None:
    verb_page = await learner_client.get("/conjugation/verbs/comer")
    trainer = await learner_client.get("/conjugation")

    assert 'href="/conjugation/practice?verb=comer"' in verb_page.text
    assert 'href="/conjugation/practice"' in trainer.text
