from enum import StrEnum
from functools import cache

from verbecc import (
    CompleteConjugator,
    LangCodeISO639_1,
    MoodEs,
    PronounEs,
    TenseEs,
    VerbNotFoundError,
)
from verbecc.src.defs.types.data import verbs as verbecc_verbs


class Tense(StrEnum):
    PRESENT = "present"
    PRETERITE = "preterite"
    IMPERFECT = "imperfect"
    FUTURE = "future"


class Person(StrEnum):
    YO = "yo"
    TU = "tu"
    EL = "el"
    NOSOTROS = "nosotros"
    VOSOTROS = "vosotros"
    ELLOS = "ellos"


TENSES = {
    Tense.PRESENT: TenseEs.Presente,
    Tense.PRETERITE: TenseEs.PretéritoPerfectoSimple,
    Tense.IMPERFECT: TenseEs.PretéritoImperfecto,
    Tense.FUTURE: TenseEs.Futuro,
}

PRONOUNS = {
    Person.YO: PronounEs.yo,
    Person.TU: PronounEs.tú,
    Person.EL: PronounEs.él,
    Person.NOSOTROS: PronounEs.nosotros,
    Person.VOSOTROS: PronounEs.vosotros,
    Person.ELLOS: PronounEs.ellos,
}

# verbecc answers "hay" for the third person of haber, which is wrong for the auxiliary,
# so its forms are written out, in the order of Person.
IRREGULAR_FORMS: dict[str, dict[Tense, tuple[str, ...]]] = {
    "haber": {
        Tense.PRESENT: ("he", "has", "ha", "hemos", "habéis", "han"),
        Tense.PRETERITE: ("hube", "hubiste", "hubo", "hubimos", "hubisteis", "hubieron"),
        Tense.IMPERFECT: ("había", "habías", "había", "habíamos", "habíais", "habían"),
        Tense.FUTURE: ("habré", "habrás", "habrá", "habremos", "habréis", "habrán"),
    }
}

# verbecc's data for pasar has endings for one tense only, and a bare stem in the rest. A
# regular verb takes the endings of a regular model of the same ending: its stem in place
# of the model's. The model must be regular in every tense, or the swap fails loudly.
REGULAR_LIKE = {"pasar": "hablar"}


@cache
def get_conjugator() -> CompleteConjugator:
    # A verb the data has no template for would otherwise be guessed by a model that
    # verbecc trains on first use, about a minute of scikit-learn work and a guess
    # at the end. The switch is read when the verb data loads, so it goes first.
    verbecc_verbs.config.ENABLE_ML_PREDICTION = False
    return CompleteConjugator(LangCodeISO639_1.es)


def conjugate(verb: str, tense: Tense, person: Person) -> str | None:
    if verb in IRREGULAR_FORMS:
        return IRREGULAR_FORMS[verb][tense][list(Person).index(person)]
    if verb in REGULAR_LIKE:
        model = REGULAR_LIKE[verb]
        form = conjugate(model, tense, person)
        if form is None:
            return None
        if not form.startswith(model[:-2]):
            raise ValueError(f"{model} is not regular in the {tense} tense")
        return verb[:-2] + form.removeprefix(model[:-2])
    try:
        conjugation = get_conjugator().conjugate_mood_tense(
            verb, MoodEs.Indicativo, TENSES[tense], conjugate_pronouns=False
        )
    except (VerbNotFoundError, IndexError):
        # IndexError: for a verb whose template only has third-person endings (resultar,
        # suceder) verbecc fails while building the voseo form.
        return None
    pronoun = PRONOUNS[person]
    return next((entry["c"][0] for entry in conjugation.get_data() if entry["pr"] == pronoun), None)
