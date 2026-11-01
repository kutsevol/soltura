from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from soltura.learner.models import KnowledgeType, MemoryCard, ReviewLog
from soltura.words.service import WordEntry
from tests.fakes import FakeLLM

NIETO = WordEntry(
    is_spanish_word=True, lemma="nieto", translation="онук", sentence="Mi nieto juega en el parque."
)
SUEGRA = WordEntry(
    is_spanish_word=True,
    lemma="suegra",
    translation="свекруха",
    sentence="Mi suegra cocina muy bien.",
)
VECINO = WordEntry(
    is_spanish_word=True, lemma="vecino", translation="сусід", sentence="Mi vecino es muy amable."
)


async def _count(session: AsyncSession, model: type) -> int:
    return (await session.execute(select(func.count()).select_from(model))).scalar_one()


async def test_a_saved_word_shows_status_both_due_dates_and_its_sentence(
    learner_client: AsyncClient, saved_words: None
) -> None:
    response = await learner_client.get("/words")

    assert response.status_code == 200
    assert "nieto" in response.text and "Вивчаю" in response.text
    assert "Упізнавання: 01.01.2030 · Згадування: 01.01.2030" in response.text
    assert "Mi nieto juega." in response.text
    assert "Упізнавання: зараз · Згадування: зараз" in response.text


async def test_the_page_lists_only_the_learners_own_words(
    learner_client: AsyncClient, saved_words: None
) -> None:
    response = await learner_client.get("/words")

    assert "Aunque llueve, salimos." in response.text
    assert "Aunque no quiero, voy." not in response.text


async def test_searching_shows_the_matching_word_and_hides_the_rest(
    learner_client: AsyncClient, saved_words: None
) -> None:
    response = await learner_client.get("/words/search", params={"q": "nie"})

    assert "nieto" in response.text
    assert "aunque" not in response.text


async def test_a_search_with_no_match_says_so(
    learner_client: AsyncClient, saved_words: None
) -> None:
    response = await learner_client.get("/words/search", params={"q": "%"})

    assert "Нічого не знайдено за запитом «%»" in response.text
    assert "nieto" not in response.text


async def test_with_no_words_the_page_says_how_to_add_one(learner_client: AsyncClient) -> None:
    response = await learner_client.get("/words")

    assert "Збережених слів ще немає" in response.text
    assert '<a href="/reading" role="button">' in response.text


async def test_looked_up_words_are_previewed_with_meaning_and_sentence(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(NIETO, SUEGRA, VECINO)

    response = await learner_client.post(
        "/words/lookup", data={"words": " nieto \nsuegra\n\nvecino\nNieto"}
    )

    assert response.status_code == 200
    for entry in (NIETO, SUEGRA, VECINO):
        assert entry.lemma in response.text and entry.translation in response.text
        assert entry.sentence in response.text
    assert len(llm.prompts) == 3
    assert response.text.count('name="lemma"') == 3
    assert "Зберегти все (3)" in response.text


async def test_a_single_word_gets_a_plain_save_button(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(NIETO)

    response = await learner_client.post("/words/lookup", data={"words": "nieto"})

    assert ">Зберегти</button>" in response.text


async def test_a_line_that_fails_does_not_stop_the_others(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(WordEntry(is_spanish_word=False, lemma="", translation="", sentence=""), NIETO)

    response = await learner_client.post("/words/lookup", data={"words": "qwxzk\nnieto"})

    assert "«qwxzk»: не схоже на іспанське слово" in response.text
    assert NIETO.sentence in response.text
    assert response.text.count('name="lemma"') == 1


async def test_a_word_already_being_learned_is_shown_saved_and_not_offered_again(
    learner_client: AsyncClient, llm: FakeLLM, saved_words: None
) -> None:
    llm.answer(NIETO, SUEGRA)

    response = await learner_client.post("/words/lookup", data={"words": "nieto\nsuegra"})

    assert "уже є у вашому словнику" in response.text
    assert response.text.count('name="lemma"') == 1
    assert 'name="lemma" value="suegra"' in response.text


async def test_looking_up_a_word_already_being_learned_changes_nothing(
    learner_client: AsyncClient, session: AsyncSession, llm: FakeLLM, saved_words: None
) -> None:
    llm.answer(NIETO)
    cards_before = await _count(session, MemoryCard)

    response = await learner_client.post("/words/lookup", data={"words": "nieto"})

    assert "уже є у вашому словнику" in response.text
    assert "/words/add" not in response.text
    assert await _count(session, MemoryCard) == cards_before
    assert await _count(session, ReviewLog) == 0


async def test_a_line_with_several_words_is_flagged_without_asking_the_model(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    response = await learner_client.post("/words/lookup", data={"words": "el piso"})

    assert "введіть одне слово в рядку" in response.text
    assert llm.prompts == []


async def test_a_twenty_first_word_is_refused_without_asking_the_model(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    words = "\n".join(f"palabra{number}" for number in range(21))

    response = await learner_client.post("/words/lookup", data={"words": words})

    assert response.status_code == 422
    assert "Не більше 20 слів" in response.text
    assert llm.prompts == []


async def test_an_empty_box_asks_for_a_word(learner_client: AsyncClient, llm: FakeLLM) -> None:
    response = await learner_client.post("/words/lookup", data={"words": " \n "})

    assert response.status_code == 422
    assert "Введіть слово" in response.text
    assert llm.prompts == []


async def test_save_all_saves_every_word_with_its_two_cards_due_now_and_lists_them(
    learner_client: AsyncClient, session: AsyncSession
) -> None:
    added = await learner_client.post(
        "/words/add",
        data={
            "lemma": ["Nieto", "suegra"],
            "sentence": [NIETO.sentence, SUEGRA.sentence],
        },
    )
    page = await learner_client.get("/words")

    assert added.status_code == 200
    assert added.headers["HX-Trigger"] == "wordsChanged"
    cards = (await session.execute(select(MemoryCard))).scalars().all()
    assert len(cards) == 4
    assert {card.knowledge_type for card in cards} == set(KnowledgeType)
    assert all(card.due <= datetime.now(UTC) for card in cards)
    for entry in (NIETO, SUEGRA):
        assert entry.lemma in page.text and entry.sentence in page.text


async def test_saving_with_mismatched_or_empty_fields_is_rejected(
    learner_client: AsyncClient, session: AsyncSession
) -> None:
    for data in (
        {"lemma": "", "sentence": "Hola."},
        {"lemma": ["nieto", "suegra"], "sentence": ["Hola."]},
        {},
    ):
        response = await learner_client.post("/words/add", data=data)

        assert response.status_code == 422
    assert await _count(session, MemoryCard) == 0
