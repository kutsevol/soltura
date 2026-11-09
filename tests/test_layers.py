import ast
import re
from collections.abc import Iterator
from pathlib import Path

import pytest

SOLTURA = Path(__file__).resolve().parent.parent / "soltura"

# The web layer: it may call use cases and name types, but call no service or repository.
WEB_FILES = {"routes.py", "views.py", "dependencies.py"}
WEB = sorted(path for path in SOLTURA.rglob("*.py") if path.name in WEB_FILES)

# What a use case calls and a route must not: a feature's services and its helpers.
LOWER_LAYER = re.compile(r"^soltura\.\w+\.(service|repository|vocabulary)$")
# The features: each has its own folder with a service of its own. Shared foundations
# (learner, language, llm, practice, srs, db) are not features.
FEATURES = (
    "conjugation",
    "grammar",
    "home",
    "onboarding",
    "reading",
    "study",
    "warmup",
    "words",
    "writing",
)
# Only the web layer may import the use cases; everything else sits below them.
MAY_IMPORT_USE_CASES = WEB_FILES


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


@pytest.mark.parametrize("path", WEB, ids=lambda path: str(path.relative_to(SOLTURA)))
def test_a_web_layer_file_calls_only_use_cases(path: Path) -> None:
    source = path.read_text()

    assert functions_imported_from_lower_layers(source) == []


def other_features_imported(source: str, feature: str) -> list[str]:
    return [
        module
        for module, _ in _imports(source)
        if module.split(".")[:1] == ["soltura"]
        and len(module.split(".")) > 1
        and module.split(".")[1] in FEATURES
        and module.split(".")[1] != feature
    ]


def test_a_feature_that_imports_another_feature_is_caught() -> None:
    source = (
        "from soltura.reading.service import prepare_text\nfrom soltura.words.service import X\n"
    )

    assert other_features_imported(source, "words") == ["soltura.reading.service"]
    assert other_features_imported("from soltura.learner.models import Learner", "words") == []


FEATURE_FILES = sorted(
    path
    for feature in FEATURES
    for path in (SOLTURA / feature).glob("*.py")
    if path.name not in WEB_FILES
)


@pytest.mark.parametrize("path", FEATURE_FILES, ids=lambda path: str(path.relative_to(SOLTURA)))
def test_a_feature_does_not_import_another_feature(path: Path) -> None:
    feature = path.parent.name

    assert other_features_imported(path.read_text(), feature) == []
