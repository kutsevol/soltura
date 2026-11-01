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


async def test_a_looked_up_word_is_previewed_with_its_meaning_and_sentence(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(NIETO)

    response = await learner_client.post("/words/lookup", data={"word": " nieto "})

    assert response.status_code == 200
    assert "nieto" in response.text and "онук" in response.text
    assert "Mi nieto juega en el parque." in response.text
    assert 'name="lemma" value="nieto"' in response.text


async def test_adding_a_word_saves_both_cards_due_now_and_lists_it(
    learner_client: AsyncClient, session: AsyncSession
) -> None:
    added = await learner_client.post(
        "/words/add", data={"lemma": "Nieto", "sentence": NIETO.sentence}
    )
    page = await learner_client.get("/words")

    assert added.status_code == 200
    assert added.headers["HX-Trigger"] == "wordsChanged"
    cards = (await session.execute(select(MemoryCard))).scalars().all()
    assert {card.knowledge_type for card in cards} == set(KnowledgeType)
    assert all(card.due <= datetime.now(UTC) for card in cards)
    assert "nieto" in page.text and NIETO.sentence in page.text


async def test_looking_up_a_word_already_being_learned_changes_nothing(
    learner_client: AsyncClient, session: AsyncSession, llm: FakeLLM, saved_words: None
) -> None:
    llm.answer(NIETO)
    cards_before = await _count(session, MemoryCard)

    response = await learner_client.post("/words/lookup", data={"word": "nieto"})

    assert "уже є у вашому словнику" in response.text
    assert "/words/add" not in response.text
    assert await _count(session, MemoryCard) == cards_before
    assert await _count(session, ReviewLog) == 0


async def test_more_than_one_word_is_refused_without_asking_the_model(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    response = await learner_client.post("/words/lookup", data={"word": "el piso"})

    assert response.status_code == 422
    assert "одне іспанське слово" in response.text
    assert llm.prompts == []


async def test_a_word_that_is_not_spanish_is_refused_with_a_message(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(WordEntry(is_spanish_word=False, lemma="", translation="", sentence=""))

    response = await learner_client.post("/words/lookup", data={"word": "asdfg"})

    assert response.status_code == 422
    assert "не схоже на іспанське слово" in response.text


async def test_adding_with_an_empty_lemma_is_rejected(learner_client: AsyncClient) -> None:
    response = await learner_client.post("/words/add", data={"lemma": "", "sentence": "Hola."})

    assert response.status_code == 422
