import re

import pytest
from httpx import AsyncClient

from soltura.templating import section_menu


def _current(path: str) -> str | None:
    menu = section_menu(path)
    assert menu is not None
    current = [item.label for item in menu.items if item.current]
    assert len(current) <= 1
    return current[0] if current else None


@pytest.mark.parametrize(
    ("path", "current"),
    [
        ("/conjugation", "Тренажер"),
        ("/conjugation/practice", "Своє дієслово"),
        ("/conjugation/endings", "Закінчення"),
        ("/conjugation/progress", "Прогрес"),
        ("/conjugation/verbs/ser", "Тренажер"),
        ("/grammar", "Правила"),
        ("/grammar/units/ser_estar", "Правила"),
        ("/grammar/progress", "Прогрес"),
        ("/reading", "Текст"),
        ("/reading/progress", "Прогрес"),
        ("/journal", "Запис"),
        ("/journal/errors", "Повторювані помилки"),
    ],
)
def test_the_page_marks_the_item_that_is_the_longest_address_above_it(
    path: str, current: str
) -> None:
    assert _current(path) == current


@pytest.mark.parametrize(
    "path", ["/", "/words", "/warmup", "/help", "/study", "/conjugations", "/readings/x"]
)
def test_a_page_of_no_module_with_a_menu_has_none(path: str) -> None:
    assert section_menu(path) is None


def _buttons(html: str) -> list[tuple[str, str, bool]]:
    nav = re.search(r'<nav class="section-menu"[^>]*>(.*?)</nav>', html, re.S)
    assert nav, "no section menu"
    return [
        (href, label, "aria-current" in attrs)
        for href, attrs, label in re.findall(
            r'<a href="([^"]+)" role="button"([^>]*)>([^<]+)</a>', nav.group(1)
        )
    ]


@pytest.mark.parametrize(
    ("path", "label", "current"),
    [
        ("/conjugation", "Дієслова", "/conjugation"),
        ("/conjugation/practice", "Дієслова", "/conjugation/practice"),
        ("/conjugation/endings", "Дієслова", "/conjugation/endings"),
        ("/conjugation/progress", "Дієслова", "/conjugation/progress"),
        ("/conjugation/verbs/comer", "Дієслова", "/conjugation"),
        ("/grammar", "Граматика", "/grammar"),
        ("/grammar/progress", "Граматика", "/grammar/progress"),
        ("/reading", "Читання", "/reading"),
        ("/reading/progress", "Читання", "/reading/progress"),
        ("/journal", "Щоденник", "/journal"),
        ("/journal/errors", "Щоденник", "/journal/errors"),
    ],
)
async def test_every_page_of_a_module_draws_its_menu_as_buttons_with_the_current_one_marked(
    learner_client: AsyncClient, path: str, label: str, current: str
) -> None:
    response = await learner_client.get(path)

    assert response.status_code == 200
    assert f'<nav class="section-menu" aria-label="{label}">' in response.text
    assert '<main class="container has-menu">' in response.text
    buttons = _buttons(response.text)
    assert [href for href, _, marked in buttons if marked] == [current]
    assert len(buttons) >= 2


async def test_from_any_page_of_the_trainer_every_other_page_is_one_button_away(
    learner_client: AsyncClient,
) -> None:
    pages = [
        "/conjugation",
        "/conjugation/practice",
        "/conjugation/endings",
        "/conjugation/progress",
    ]
    for path in pages:
        hrefs = {href for href, _, _ in _buttons((await learner_client.get(path)).text)}
        assert hrefs == set(pages)

    verb_page = await learner_client.get("/conjugation/verbs/comer")
    assert {href for href, _, _ in _buttons(verb_page.text)} == set(pages)


@pytest.mark.parametrize("path", ["/", "/words", "/help"])
async def test_a_page_outside_the_modules_has_no_menu(
    learner_client: AsyncClient, path: str
) -> None:
    response = await learner_client.get(path)

    assert 'class="section-menu"' not in response.text
    assert '<main class="container">' in response.text
