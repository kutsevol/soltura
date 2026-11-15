import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache

from soltura.conjugation.forms import Person, Tense, conjugate
from soltura.conjugation.service import regular_endings

STEM_CHANGE_PERSONS = (Person.YO, Person.TU, Person.EL, Person.ELLOS)
BUILT_ON_INFINITIVE = (Tense.FUTURE, Tense.CONDITIONAL)
SPELLING_MARKER = {"car": "qu", "gar": "gu", "zar": "c"}


def _plain(text: str) -> str:
    # A written accent is no part of a comparison of forms: the library writes rió and ví where
    # the spelling of one-syllable words has rio and vi.
    return "".join(
        char for char in unicodedata.normalize("NFD", text) if not unicodedata.combining(char)
    )


def _infinitive(verb: str) -> str:
    # The future of oír is oiré: the accent of the infinitive is not written inside the word.
    return verb.replace("ír", "ir")


def _join(stem: str, ending: str) -> str:
    # Where a stem meets an ending the spelling adjusts: ri + ió is rió, and segu + o is sigo.
    if stem.endswith("i") and ending[:1] in ("i", "í"):
        return stem + ending[1:]
    if stem.endswith("gu") and ending[:1] in ("o", "a"):
        return stem[:-1] + ending
    return stem + ending


@dataclass(frozen=True)
class Form:
    verb: str
    tense: Tense
    person: Person
    actual: str
    regular: str

    @property
    def stem(self) -> str:
        return self.verb[:-2]

    @property
    def ending(self) -> str:
        return self.regular.removeprefix(
            _infinitive(self.verb) if self.tense in BUILT_ON_INFINITIVE else self.stem
        )

    @property
    def is_regular(self) -> bool:
        return _plain(self.actual) == _plain(self.regular)

    def equals(self, stem: str) -> bool:
        return _plain(self.actual) == _plain(_join(stem, self.ending))


@dataclass(frozen=True)
class Pattern:
    id: str
    title: str
    rule: str
    tenses: tuple[Tense, ...]
    applies: Callable[[Form], bool]


@dataclass(frozen=True)
class PatternExample:
    tense: Tense
    forms: list[str]


@dataclass(frozen=True)
class PatternNote:
    pattern: Pattern
    examples: list[PatternExample]


@cache
def _endings() -> dict[Tense, dict[str, list[str]]]:
    return regular_endings()


def regular_form(verb: str, tense: Tense, person: Person) -> str:
    # The form a regular verb of the same ending would have: its stem, or for the future and
    # the conditional the whole infinitive, and the ending of the model verb.
    key = "ir" if verb.endswith("ír") else verb[-2:]
    stem = _infinitive(verb) if tense in BUILT_ON_INFINITIVE else verb[:-2]
    return stem + _endings()[tense][key][list(Person).index(person)]


def _swap_last(text: str, old: str, new: str) -> str | None:
    index = text.rfind(old)
    return None if index < 0 else f"{text[:index]}{new}{text[index + len(old) :]}"


def _stem_change(old: str, new: str) -> Callable[[Form], bool]:
    def applies(form: Form) -> bool:
        if form.tense != Tense.PRESENT or form.person not in STEM_CHANGE_PERSONS:
            return False
        changed = _swap_last(form.stem, old, new)
        return changed is not None and not form.is_regular and form.equals(changed)

    return applies


def _is_go(form: Form) -> bool:
    return (
        form.tense == Tense.PRESENT
        and form.person == Person.YO
        and form.actual.endswith("go")
        and not form.regular.endswith("go")
        # seguir → sigo is a stem change with the spelling of the g, not a -go verb.
        and not form.stem.endswith(("gu", "qu"))
    )


def _is_zco(form: Form) -> bool:
    return (
        form.tense == Tense.PRESENT
        and form.person == Person.YO
        and form.actual.endswith("zco")
        and not form.is_regular
    )


def _is_strong_preterite(form: Form) -> bool:
    # A strong preterite has no written accent on yo (tuve, fui) and a stem or endings of its
    # own. Dar and ver only take the endings of the other conjugations (di, dio; vi, vio).
    yo = conjugate(form.verb, Tense.PRETERITE, Person.YO)
    other = "er" if form.verb.endswith("ar") else "ir"
    other_ending = _endings()[Tense.PRETERITE][other][list(Person).index(form.person)]
    return (
        form.tense == Tense.PRETERITE
        and yo is not None
        and yo[-1] not in "éí"
        and not form.is_regular
        and _plain(form.actual) != _plain(_join(form.stem, other_ending))
    )


def _is_raised_preterite(form: Form) -> bool:
    # Only the verbs on -ir whose yo is regular: poder and venir have a strong preterite.
    yo = conjugate(form.verb, Tense.PRETERITE, Person.YO)
    if (
        form.tense != Tense.PRETERITE
        or form.person not in (Person.EL, Person.ELLOS)
        or not form.verb.endswith(("ir", "ír"))
        or yo is None
        or _plain(yo) != _plain(regular_form(form.verb, Tense.PRETERITE, Person.YO))
    ):
        return False
    return any(
        (changed := _swap_last(form.stem, old, new)) is not None
        and not form.is_regular
        and form.equals(changed)
        for old, new in (("e", "i"), ("o", "u"))
    )


def _is_short_future(form: Form) -> bool:
    return form.tense in BUILT_ON_INFINITIVE and not form.is_regular


def _is_spelling_change(form: Form) -> bool:
    marker = SPELLING_MARKER.get(form.verb[-3:])
    if marker is None or form.tense != Tense.PRETERITE or form.person != Person.YO:
        return False
    changed = form.actual[len(form.stem) - 1 :]
    return not form.is_regular and changed.startswith(marker) and not changed.startswith("z")


def _is_y_preterite(form: Form) -> bool:
    return (
        form.tense == Tense.PRETERITE
        and form.person in (Person.EL, Person.ELLOS)
        and not form.is_regular
        and form.actual.endswith(("yó", "yeron"))
    )


def _is_irregular_imperfect(form: Form) -> bool:
    return form.tense == Tense.IMPERFECT and not form.is_regular


PATTERNS = (
    Pattern(
        "stem_e_ie",
        "e → ie в корені",
        "У деяких дієслів, коли наголос падає на корінь, e змінюється на ie: pensar → pienso, "
        "piensas, piensa, piensan. У формах nosotros і vosotros наголос не на корені, тому там "
        "змін немає: pensamos, pensáis.",
        (Tense.PRESENT,),
        _stem_change("e", "ie"),
    ),
    Pattern(
        "stem_o_ue",
        "o → ue в корені",
        "У деяких дієслів, коли наголос падає на корінь, o змінюється на ue: poder → puedo, "
        "puedes, puede, pueden. У формах nosotros і vosotros змін немає: podemos, podéis.",
        (Tense.PRESENT,),
        _stem_change("o", "ue"),
    ),
    Pattern(
        "stem_e_i",
        "e → i в корені",
        "У деяких дієслів на -ir, коли наголос падає на корінь, e змінюється на i: pedir → "
        "pido, pides, pide, piden. У формах nosotros і vosotros змін немає: pedimos, pedís.",
        (Tense.PRESENT,),
        _stem_change("e", "i"),
    ),
    Pattern(
        "stem_u_ue",
        "u → ue в корені",
        "Єдине дієслово з такою зміною — jugar: juego, juegas, juega, juegan. У формах "
        "nosotros і vosotros змін немає: jugamos, jugáis.",
        (Tense.PRESENT,),
        _stem_change("u", "ue"),
    ),
    Pattern(
        "go_yo",
        "Форма yo на -go",
        "Кілька дуже частих дієслів мають yo на -go: tener → tengo, hacer → hago, poner → "
        "pongo, salir → salgo, venir → vengo, decir → digo. Окрім цього, tener і venir у "
        "формах tú, él, ellos змінюють e → ie (tienes), а decir — e → i (dices).",
        (Tense.PRESENT,),
        _is_go,
    ),
    Pattern(
        "zco_yo",
        "Форма yo на -zco",
        "Дієслова на -cer і -cir після голосної здебільшого мають yo на -zco: conocer → "
        "conozco, parecer → parezco, conducir → conduzco. Винятки: hacer → hago, decir → digo.",
        (Tense.PRESENT,),
        _is_zco,
    ),
    Pattern(
        "strong_preterite",
        "«Сильний» претерит",
        "У деяких дієслів корінь претериту змінений, а форми yo і él пишуться без знака "
        "наголосу (tuve, tuvo; fui, fue), на відміну від правильних (hablé, habló). Корені: "
        "tener → tuv-, hacer → hic- (él hizo), poder → pud-, poner → pus-, venir → vin-, "
        "decir → dij- (ellos dijeron).",
        (Tense.PRETERITE,),
        _is_strong_preterite,
    ),
    Pattern(
        "raised_preterite",
        "e → i, o → u в претериті",
        "Майже всі дієслова на -ir, у яких у теперішньому часі змінюється e чи o, у претериті "
        "мають у формах él і ellos e → i або o → u: pedir → pidió, pidieron; dormir → durmió, "
        "durmieron; sentir → sintió, sintieron.",
        (Tense.PRETERITE,),
        _is_raised_preterite,
    ),
    Pattern(
        "short_future",
        "Змінений корінь у майбутньому часі та умовному способі",
        "Деякі дієслова мають у майбутньому часі та в умовному способі змінений корінь, а "
        "закінчення звичайні: tener → tendr-, hacer → har-, poder → podr-, poner → pondr-, "
        "venir → vendr-, decir → dir-, saber → sabr-, querer → querr-, salir → saldr-, "
        "haber → habr- (habrá).",
        (Tense.FUTURE, Tense.CONDITIONAL),
        _is_short_future,
    ),
    Pattern(
        "spelling_yo",
        "Зміна написання в yo претериту",
        "Через правила написання перед e в формі yo претериту пишемо: -car → -qué (buscar → "
        "busqué), -gar → -gué (llegar → llegué), -zar → -cé (empezar → empecé).",
        (Tense.PRETERITE,),
        _is_spelling_change,
    ),
    Pattern(
        "y_preterite",
        "i → y між голосними",
        "Між голосними i стає y у формах él і ellos претериту: leer → leyó, leyeron; caer → "
        "cayó, cayeron; construir → construyó, construyeron. Виняток: traer → trajo, trajeron.",
        (Tense.PRETERITE,),
        _is_y_preterite,
    ),
    Pattern(
        "irregular_imperfect",
        "Неправильний imperfecto",
        "Лише три дієслова мають неправильний imperfecto: ser (era), ir (iba), ver (veía) і "
        "похідні від ver (preveía). Усі інші утворюють його за правилом.",
        (Tense.IMPERFECT,),
        _is_irregular_imperfect,
    ),
)


def _forms(verb: str, tenses: tuple[Tense, ...]) -> list[Form]:
    forms = []
    for tense in tenses:
        for person in Person:
            actual = conjugate(verb, tense, person)
            if actual is not None:
                forms.append(Form(verb, tense, person, actual, regular_form(verb, tense, person)))
    return forms


def pattern_notes(verb: str, tense: Tense | None = None) -> list[PatternNote]:
    # The patterns a verb follows, found by comparing each of its forms with the regular form,
    # and for each the forms that show it. With a tense, only the patterns that touch it.
    notes = []
    for pattern in PATTERNS:
        if tense is not None and tense not in pattern.tenses:
            continue
        examples = []
        for pattern_tense in pattern.tenses:
            shown = [
                form.actual for form in _forms(verb, (pattern_tense,)) if pattern.applies(form)
            ]
            if shown:
                examples.append(PatternExample(pattern_tense, shown))
        if examples:
            notes.append(PatternNote(pattern, examples))
    return notes
