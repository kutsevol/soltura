from dataclasses import dataclass
from pathlib import Path

from fastapi.templating import Jinja2Templates


@dataclass(frozen=True)
class NavItem:
    href: str
    label: str
    icon: str


# The bottom tab bar, in order. A screen joins it in the change that adds the screen,
# so no tab ever points at a page that does not exist yet.
NAV: list[NavItem] = [
    NavItem(href="/", label="Головна", icon="home"),
    NavItem(href="/warmup", label="Розминка", icon="zap"),
    NavItem(href="/reading", label="Читання", icon="book"),
]

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["nav"] = NAV
