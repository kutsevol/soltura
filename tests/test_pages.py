import os
import re
from pathlib import Path

import pytest
from httpx import AsyncClient

from soltura import templating
from soltura.templating import NAV, asset_version

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
        ("/help", "/help"),
        ("/onboarding", None),
    ],
)
async def test_every_page_shows_the_tab_bar_with_its_own_tab_marked(
    learner_client: AsyncClient, path: str, current: str | None
) -> None:
    response = await learner_client.get(path)

    assert response.status_code == 200
    assert tabs(response.text) == {item.href: item.href == current for item in NAV}


@pytest.mark.parametrize("path", ["/", "/reading", "/warmup", "/words", "/help", "/onboarding"])
async def test_every_page_has_the_help_link_in_the_title_bar(
    learner_client: AsyncClient, path: str
) -> None:
    response = await learner_client.get(path)

    titlebar = response.text[: response.text.index("</header>")]
    assert '<a href="/help" class="help-link" aria-label="Як це працює">?</a>' in titlebar


async def test_the_stylesheet_is_served(learner_client: AsyncClient) -> None:
    response = await learner_client.get("/static/app.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


async def test_the_page_links_the_stylesheet_with_the_version_of_the_file(
    learner_client: AsyncClient,
) -> None:
    page = (await learner_client.get("/help")).text

    assert f'/static/app.css?v={asset_version("app.css")}"' in page


def test_the_asset_version_changes_when_the_file_does(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(templating, "STATIC_DIR", tmp_path)
    stylesheet = tmp_path / "app.css"
    stylesheet.write_text("body {}")
    os.utime(stylesheet, (1_000_000, 1_000_000))
    before = asset_version("app.css")

    os.utime(stylesheet, (2_000_000, 2_000_000))

    assert asset_version("app.css") != before


async def test_every_screen_the_help_page_mentions_is_a_working_link(
    learner_client: AsyncClient,
) -> None:
    page = (await learner_client.get("/help")).text
    links = set(re.findall(r'href="(/[^"]*)"', page[page.index("<main") : page.index("</main>")]))

    assert {item.href for item in NAV} - {"/", "/help"} <= links
    assert "/onboarding" in links
    for link in links:
        assert (await learner_client.get(link)).status_code == 200, link
