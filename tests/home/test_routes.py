from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.grammar.units import all_units
from soltura.learner.models import Learner, MemoryCard, PlacementRun
from soltura.reading.topics import TOPICS
from soltura.templating import NAV
from soltura.use_cases.grammar import start_unit


async def test_the_main_button_starts_the_warmup_and_counts_due_cards(
    learner_client: AsyncClient, saved_word: None
) -> None:
    response = await learner_client.get("/")

    assert response.status_code == 200
    assert "Карток до повторення: 2" in response.text
    assert "Слів у вивченні: 1" in response.text
    assert '<a href="/warmup" role="button">' in response.text
    assert '<a href="/reading" role="button">' not in response.text


async def test_the_due_count_is_words_only(
    learner_client: AsyncClient, saved_word: None, due_conjugation_card: MemoryCard
) -> None:
    response = await learner_client.get("/")

    assert "Карток до повторення: 2" in response.text


async def test_the_hub_lists_the_trainer_with_its_due_count(
    learner_client: AsyncClient, due_conjugation_card: MemoryCard
) -> None:
    response = await learner_client.get("/")

    assert '<h3><a href="/conjugation">Дієслова</a></h3>' in response.text
    assert "Форм до повторення: 1" in response.text


async def test_the_main_button_offers_reading_when_nothing_is_due(
    learner_client: AsyncClient,
) -> None:
    response = await learner_client.get("/")

    assert response.status_code == 200
    assert "Карток до повторення" not in response.text
    assert "Слів у вивченні: 0" in response.text
    assert '<a href="/reading" role="button">' in response.text
    assert '<a href="/warmup" role="button">' not in response.text


async def test_the_hub_does_not_repeat_the_tab_bar_as_cards(learner_client: AsyncClient) -> None:
    response = await learner_client.get("/")

    for item in NAV:
        assert f'<h3><a href="{item.href}">' not in response.text


async def test_the_placement_tile_invites_to_the_test_before_a_run(
    learner_client: AsyncClient,
) -> None:
    response = await learner_client.get("/")

    assert '<h3><a href="/onboarding">Визначення рівня</a></h3>' in response.text
    assert "/onboarding/result" not in response.text


async def test_the_placement_tile_shows_the_result_and_links_to_it(
    learner_client: AsyncClient, placement_run: PlacementRun
) -> None:
    response = await learner_client.get("/")

    assert '<h3><a href="/onboarding/result">Визначення рівня</a></h3>' in response.text
    assert "Знайомо 500 найчастотніших слів" in response.text


async def test_the_placement_tile_says_when_no_group_was_passed(
    learner_client: AsyncClient, failed_placement_run: PlacementRun
) -> None:
    response = await learner_client.get("/")

    assert "Жодну групу слів не пройдено" in response.text


async def test_a_learner_without_saved_words_is_offered_the_help(
    learner_client: AsyncClient,
) -> None:
    response = await learner_client.get("/")

    assert "Вперше тут?" in response.text
    assert '<a href="/help">Як це працює</a>' in response.text


async def test_the_help_offer_goes_away_after_the_first_saved_word(
    learner_client: AsyncClient, saved_word: None
) -> None:
    response = await learner_client.get("/")

    assert "Вперше тут?" not in response.text


async def test_the_hub_shows_the_known_total_and_links_to_the_words_page(
    learner_client: AsyncClient, vocabulary_words: None
) -> None:
    response = await learner_client.get("/")

    assert response.status_code == 200
    assert '<a href="/words">Знаю слів: 2 з 5</a>' in response.text


async def test_a_learner_without_words_sees_zero_known_words(
    learner_client: AsyncClient,
) -> None:
    response = await learner_client.get("/")

    assert response.status_code == 200
    assert '<a href="/words">Знаю слів: 0 з 0</a>' in response.text


async def test_the_hub_lists_grammar_with_the_next_lesson_when_nothing_is_due(
    learner_client: AsyncClient,
) -> None:
    response = await learner_client.get("/")

    assert '<h3><a href="/grammar">Граматика</a></h3>' in response.text
    assert f"Наступне правило: {all_units()[0].title}" in response.text


async def test_the_grammar_tile_counts_the_exercises_due(
    learner_client: AsyncClient, session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    await start_unit(session, learner.id, all_units()[0].id, datetime(2020, 1, 1, tzinfo=UTC))

    response = await learner_client.get("/")

    assert "Вправ до повторення: 6" in response.text


async def test_the_hub_links_to_the_journal(learner_client: AsyncClient) -> None:
    response = await learner_client.get("/")

    assert '<h3><a href="/journal">Щоденник</a></h3>' in response.text


async def test_the_hub_offers_to_start_a_session(learner_client: AsyncClient) -> None:
    response = await learner_client.get("/")

    assert (
        '<a href="/study" role="button" class="secondary outline">Почати сесію</a>' in response.text
    )
    assert "Продовжити сесію" not in response.text


async def test_the_hub_continues_an_open_session_instead(learner_client: AsyncClient) -> None:
    await learner_client.post("/study/start", data={"topic": TOPICS[0].label})

    response = await learner_client.get("/")

    assert f"Сесія: {TOPICS[0].label}" in response.text
    assert '<a href="/study" role="button">Продовжити сесію</a>' in response.text
    assert "Почати сесію" not in response.text
    assert '<a href="/warmup" role="button">' not in response.text
