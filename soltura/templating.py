from dataclasses import dataclass
from pathlib import Path

from fastapi.templating import Jinja2Templates


@dataclass(frozen=True)
class NavItem:
    href: str
    label: str
    icon: str
    purpose: str
    tone: str = ""


# The bottom tab bar, in order. A screen joins it in the change that adds the screen,
# so no tab ever points at a page that does not exist yet.
NAV: list[NavItem] = [
    NavItem(href="/", label="Головна", icon="home", purpose="Що робити зараз"),
    NavItem(
        href="/warmup",
        label="Розминка",
        icon="zap",
        tone="warmup",
        purpose="Короткі вправи на слова, які ви зберегли",
    ),
    NavItem(
        href="/reading",
        label="Читання",
        icon="book",
        tone="reading",
        purpose="Текст під ваш рівень; тапніть слово, щоб побачити переклад і зберегти",
    ),
    NavItem(
        href="/words",
        label="Слова",
        icon="list",
        tone="words",
        purpose="Усі збережені слова: коли їх повторювати і з яких речень вони",
    ),
    NavItem(
        href="/help",
        label="Як це працює",
        icon="info",
        tone="help",
        purpose="Від тапу на слово до розминки, на одному прикладі",
    ),
]

# Reached from the hub only: the bar already holds five tabs.
TRAINER = NavItem(
    href="/conjugation",
    label="Дієслова",
    icon="zap",
    tone="conjugation",
    purpose="Форми дієслів: впишіть форму для особи й часу",
)

STATIC_DIR = Path(__file__).parent / "static"


def asset_version(path: str) -> int:
    # Starlette sends no Cache-Control for static files, so a browser may keep a stale
    # stylesheet; the file's mtime in the URL makes every edit a new address.
    return int((STATIC_DIR / path).stat().st_mtime)


templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["nav"] = NAV
templates.env.globals["trainer"] = TRAINER
templates.env.globals["asset_version"] = asset_version
