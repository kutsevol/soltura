from pathlib import Path

from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[1]


def _alembic_config(database_url: str) -> Config:
    config = Config(ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_migrations_match_the_models(database_url: str) -> None:
    command.check(_alembic_config(database_url))


def test_migrations_downgrade_and_upgrade_again(database_url: str) -> None:
    config = _alembic_config(database_url)

    command.downgrade(config, "base")
    command.upgrade(config, "head")
