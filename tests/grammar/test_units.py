import pytest

from soltura.grammar.units import (
    GAP,
    SEPARATOR,
    GrammarUnit,
    all_units,
    exercise_key,
    get_unit,
    next_unit,
    parse_exercise_key,
    started_unit_ids,
    unit_keys,
)

UNITS = all_units()


def test_the_registry_lists_the_units_in_teaching_order() -> None:
    assert [unit.id for unit in UNITS] == ["gender_of_nouns", "ser_estar", "por_para"]
    assert sorted((unit.level, unit.order) for unit in UNITS) == [
        (unit.level, unit.order) for unit in UNITS
    ]


def test_every_unit_has_its_own_id_and_place_in_the_order() -> None:
    assert len({unit.id for unit in UNITS}) == len(UNITS)
    assert len({(unit.level, unit.order) for unit in UNITS}) == len(UNITS)


@pytest.mark.parametrize("unit", UNITS, ids=lambda unit: unit.id)
def test_a_unit_has_a_lesson_and_six_exercises_with_unique_ids(unit: GrammarUnit) -> None:
    assert SEPARATOR not in unit.id
    assert unit.lesson.points and unit.lesson.examples
    assert len(unit.exercises) == 6
    assert len({exercise.id for exercise in unit.exercises}) == 6
    assert all(SEPARATOR not in exercise.id for exercise in unit.exercises)


@pytest.mark.parametrize("unit", UNITS, ids=lambda unit: unit.id)
def test_an_exercise_has_one_gap_and_an_answer_the_learner_can_give(unit: GrammarUnit) -> None:
    for exercise in unit.exercises:
        assert exercise.sentence.count(GAP) == 1, exercise.id
        assert exercise.translation and exercise.note, exercise.id
        if exercise.is_choice:
            assert 2 <= len(exercise.options) <= 3, exercise.id
            assert len(set(exercise.options)) == len(exercise.options), exercise.id
            assert exercise.answer in exercise.options, exercise.id


def test_an_exercise_key_names_its_unit_and_exercise() -> None:
    unit = UNITS[0]
    key = exercise_key(unit.id, unit.exercises[2].id)

    parsed = parse_exercise_key(key)

    assert parsed == (unit, unit.exercises[2])
    assert unit_keys(unit) == [exercise_key(unit.id, exercise.id) for exercise in unit.exercises]


@pytest.mark.parametrize("key", [None, "", "ser_estar", "ser_estar|zzz", "nothing|e1", "a|b|c"])
def test_a_key_that_names_no_exercise_parses_to_nothing(key: str | None) -> None:
    assert parse_exercise_key(key) is None


def test_the_next_unit_is_the_first_one_not_started() -> None:
    started = started_unit_ids(set(unit_keys(UNITS[0])) | set(unit_keys(UNITS[1])))

    assert started == {UNITS[0].id, UNITS[1].id}
    assert next_unit(started) == UNITS[2]
    assert next_unit(set()) == UNITS[0]
    assert next_unit({unit.id for unit in UNITS}) is None


def test_a_unit_is_found_by_its_id() -> None:
    assert get_unit("ser_estar") is not None
    assert get_unit("nothing") is None
