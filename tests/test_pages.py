import re

import pytest
from httpx import AsyncClient

from soltura.templating import NAV

TAB = re.compile(r'<a href="(?P<href>[^"]+)"(?P<current> aria-current="page")?>')


def tabs(html: str) -> dict[str, bool]:
    nav = html[html.index('<nav class="tabbar"') :]
    return {match["href"]: bool(match["current"]) for match in TAB.finditer(nav)}


@pytest.mark.parametrize(
    ("path", "current"),
    [
        ("/reading", "/reading"),
        ("/warmup", "/warmup"),
        ("/words", "/words"),
        ("/onboarding", None),
    ],
)
async def test_every_page_shows_the_tab_bar_with_its_own_tab_marked(
    learner_client: AsyncClient, path: str, current: str | None
) -> None:
    response = await learner_client.get(path)

    assert response.status_code == 200
    assert tabs(response.text) == {item.href: item.href == current for item in NAV}


async def test_the_stylesheet_is_served(learner_client: AsyncClient) -> None:
    response = await learner_client.get("/static/app.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
