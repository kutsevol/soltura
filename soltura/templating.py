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

GRAMMAR = NavItem(
    href="/grammar",
    label="Граматика",
    icon="book",
    tone="grammar",
    purpose="Правило з прикладами, потім вправи на нього",
)

JOURNAL = NavItem(
    href="/journal",
    label="Щоденник",
    icon="book",
    tone="journal",
    purpose="Напишіть кілька речень іспанською і побачте виправлення",
)


@dataclass(frozen=True)
class MenuItem:
    href: str
    label: str
    current: bool = False


@dataclass(frozen=True)
class SectionMenu:
    label: str
    items: list[MenuItem]


# A module with more than one page: its pages, in order, each reachable from every other.
# The first item is the module's own address.
SECTIONS: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "/conjugation": (
        "Дієслова",
        [
            ("/conjugation", "Тренажер"),
            ("/conjugation/practice", "Своє дієслово"),
            ("/conjugation/endings", "Закінчення"),
            ("/conjugation/progress", "Прогрес"),
        ],
    ),
    "/grammar": (
        "Граматика",
        [("/grammar", "Правила"), ("/grammar/progress", "Прогрес")],
    ),
    "/reading": (
        "Читання",
        [("/reading", "Текст"), ("/reading/progress", "Прогрес")],
    ),
    "/journal": (
        "Щоденник",
        [("/journal", "Запис"), ("/journal/errors", "Повторювані помилки")],
    ),
}


def _within(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(f"{prefix}/")


def section_menu(path: str) -> SectionMenu | None:
    # The menu of the module a page belongs to, with the item that is the longest address
    # above the page marked: a verb page marks the trainer, a lesson marks the rules.
    for prefix, (label, pages) in SECTIONS.items():
        if not _within(path, prefix):
            continue
        current = max((href for href, _ in pages if _within(path, href)), key=len, default=prefix)
        return SectionMenu(label, [MenuItem(href, text, href == current) for href, text in pages])
    return None


STATIC_DIR = Path(__file__).parent / "static"


def asset_version(path: str) -> int:
    # Starlette sends no Cache-Control for static files, so a browser may keep a stale
    # stylesheet; the file's mtime in the URL makes every edit a new address.
    return int((STATIC_DIR / path).stat().st_mtime)


templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["nav"] = NAV
templates.env.globals["trainer"] = TRAINER
templates.env.globals["grammar_module"] = GRAMMAR
templates.env.globals["journal_module"] = JOURNAL
templates.env.globals["asset_version"] = asset_version
templates.env.globals["section_menu"] = section_menu
