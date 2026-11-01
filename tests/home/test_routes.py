from httpx import AsyncClient

from soltura.templating import NAV


async def test_the_main_button_starts_the_warmup_and_counts_due_cards(
    learner_client: AsyncClient, saved_word: None
) -> None:
    response = await learner_client.get("/")

    assert response.status_code == 200
    assert "Карток до повторення: 2" in response.text
    assert "Слів у вивченні: 1" in response.text
    assert '<a href="/warmup" role="button">' in response.text
    assert '<a href="/reading" role="button">' not in response.text


async def test_the_main_button_offers_reading_when_nothing_is_due(
    learner_client: AsyncClient,
) -> None:
    response = await learner_client.get("/")

    assert response.status_code == 200
    assert "Карток до повторення" not in response.text
    assert "Слів у вивченні: 0" in response.text
    assert '<a href="/reading" role="button">' in response.text
    assert '<a href="/warmup" role="button">' not in response.text


async def test_every_screen_is_listed_with_its_purpose(learner_client: AsyncClient) -> None:
    response = await learner_client.get("/")

    for item in NAV:
        if item.href != "/":
            assert f'<h3><a href="{item.href}">{item.label}</a></h3>' in response.text
            assert item.purpose in response.text
    assert '<a href="/onboarding">' in response.text


async def test_a_learner_without_saved_words_is_offered_the_help(
    learner_client: AsyncClient,
) -> None:
    response = await learner_client.get("/")

    assert "Вперше тут?" in response.text
    assert '<a href="/help" role="button" class="outline">' in response.text


async def test_the_help_offer_goes_away_after_the_first_saved_word(
    learner_client: AsyncClient, saved_word: None
) -> None:
    response = await learner_client.get("/")

    assert "Вперше тут?" not in response.text
