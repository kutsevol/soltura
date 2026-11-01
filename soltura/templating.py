from dataclasses import dataclass
from pathlib import Path

from fastapi.templating import Jinja2Templates


@dataclass(frozen=True)
class NavItem:
    href: str
    label: str
    icon: str
    purpose: str


# The bottom tab bar, in order. A screen joins it in the change that adds the screen,
# so no tab ever points at a page that does not exist yet.
NAV: list[NavItem] = [
    NavItem(href="/", label="Головна", icon="home", purpose="Що робити зараз"),
    NavItem(
        href="/warmup",
        label="Розминка",
        icon="zap",
        purpose="Короткі вправи на слова, які ви зберегли",
    ),
    NavItem(
        href="/reading",
        label="Читання",
        icon="book",
        purpose="Текст під ваш рівень; тапніть слово, щоб побачити переклад і зберегти",
    ),
    NavItem(
        href="/words",
        label="Слова",
        icon="list",
        purpose="Усі збережені слова: коли їх повторювати і з яких речень вони",
    ),
    NavItem(
        href="/help",
        label="Як це працює",
        icon="info",
        purpose="Від тапу на слово до розминки, на одному прикладі",
    ),
]

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["nav"] = NAV
