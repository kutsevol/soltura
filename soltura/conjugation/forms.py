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

# verbecc answers "hay" for the third person of haber, which is wrong for the auxiliary.
UNSUPPORTED_VERBS = frozenset({"haber"})


@cache
def get_conjugator() -> CompleteConjugator:
    # A verb the data has no template for would otherwise be guessed by a model that
    # verbecc trains on first use, about a minute of scikit-learn work and a guess
    # at the end. The switch is read when the verb data loads, so it goes first.
    verbecc_verbs.config.ENABLE_ML_PREDICTION = False
    return CompleteConjugator(LangCodeISO639_1.es)


def conjugate(verb: str, tense: Tense, person: Person) -> str | None:
    if verb in UNSUPPORTED_VERBS:
        return None
    try:
        conjugation = get_conjugator().conjugate_mood_tense(
            verb, MoodEs.Indicativo, TENSES[tense], conjugate_pronouns=False
        )
    except (VerbNotFoundError, IndexError):
        # IndexError: for a verb whose template only has third-person endings (pasar,
        # resultar, suceder) verbecc fails while building the voseo form.
        return None
    pronoun = PRONOUNS[person]
    return next((entry["c"][0] for entry in conjugation.get_data() if entry["pr"] == pronoun), None)
