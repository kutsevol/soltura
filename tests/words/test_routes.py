from httpx import AsyncClient


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
