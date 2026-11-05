import ast
import re
from collections.abc import Iterator
from pathlib import Path

import pytest

SOLTURA = Path(__file__).resolve().parent.parent / "soltura"

# Every feature's routes call only use cases.
ROUTES = sorted(SOLTURA.glob("*/routes.py"))

# What a use case calls and a route must not: a feature's services and its helpers.
LOWER_LAYER = re.compile(r"^soltura\.\w+\.(service|repository|vocabulary|screens)$")
# Only these may import the use cases; everything else sits below them.
MAY_IMPORT_USE_CASES = {"routes.py", "views.py"}


def _imports(source: str) -> Iterator[tuple[str, list[str]]]:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module:
            yield node.module, [alias.name for alias in node.names]
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, []


def imports_use_cases(source: str) -> bool:
    return any(
        module == "soltura.use_cases"
        or module.startswith("soltura.use_cases.")
        or (module == "soltura" and "use_cases" in names)
        for module, names in _imports(source)
    )


def functions_imported_from_lower_layers(source: str) -> list[str]:
    # Types and constants (CapWords, UPPER_CASE) are data the route may name; a lowercase
    # name from a service or repository is a function it should not call.
    return [
        f"{module}.{name}"
        for module, names in _imports(source)
        if LOWER_LAYER.match(module)
        for name in names
        if not name[0].isupper()
    ]


def test_a_service_that_imports_a_use_case_is_caught() -> None:
    assert imports_use_cases("from soltura.use_cases.warmup import answer_item")
    assert imports_use_cases("import soltura.use_cases.warmup")
    assert imports_use_cases("from soltura import use_cases")
    assert not imports_use_cases("from soltura.warmup.service import answer_item")


def test_a_route_that_imports_a_service_function_is_caught() -> None:
    source = (
        "from soltura.warmup.service import WarmupItem, answer_item\n"
        "from soltura.learner.repository import get_saved_words, SavedWord\n"
        "from soltura.use_cases.warmup import build_warmup\n"
    )

    assert functions_imported_from_lower_layers(source) == [
        "soltura.warmup.service.answer_item",
        "soltura.learner.repository.get_saved_words",
    ]


def test_nothing_below_the_use_cases_imports_them() -> None:
    offenders = [
        str(path.relative_to(SOLTURA))
        for path in SOLTURA.rglob("*.py")
        if "use_cases" not in path.parts
        and path.name not in MAY_IMPORT_USE_CASES
        and imports_use_cases(path.read_text())
    ]

    assert offenders == []


@pytest.mark.parametrize("path", ROUTES, ids=lambda path: path.parent.name)
def test_a_route_calls_only_use_cases(path: Path) -> None:
    source = path.read_text()

    assert functions_imported_from_lower_layers(source) == []
