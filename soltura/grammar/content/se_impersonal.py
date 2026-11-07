from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="se_impersonal",
    level="B1",
    order=50,
    title="se безособове й пасивне: se habla español, se venden pisos",
    lesson=Lesson(
        points=(
            "Se плюс дієслово в третій особі — коли не кажемо, хто діє: se habla español, se vive bien aquí.",
            "Дієслово узгоджується з іменником, що йде після нього: se vende una casa, se venden casas.",
            "Якщо після дієслова стоїть конкретна особа з a, дієслово лишається в однині: se busca a los culpables, se ve a los niños.",
            "Так пишуть оголошення й правила: se alquila piso, se prohíbe fumar.",
            "Se me плюс дієслово — «трапилося зі мною, не навмисно»: se me cayó el vaso — у мене впала склянка; se me olvidó la llave — я забув ключ. Дієслово узгоджується з тим, що впало чи забулося: se me cayeron las llaves.",
        ),
        examples=(
            Example(spanish="En España se cena tarde.", ukrainian="В Іспанії вечеряють пізно."),
            Example(spanish="Se vende una bicicleta.", ukrainian="Продається велосипед."),
            Example(
                spanish="Se venden pisos en el centro.", ukrainian="Продаються квартири в центрі."
            ),
            Example(spanish="Se prohíbe fumar.", ukrainian="Курити заборонено."),
            Example(spanish="Se me ha caído el móvil.", ukrainian="У мене впав телефон."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Se ___ dos coches usados.",
            translation="Продаються дві вживані машини.",
            options=("vende", "venden"),
            answer="venden",
            note="Dos coches у множині, тому venden.",
        ),
        Exercise(
            id="e2",
            sentence="En Francia ___ cena temprano.",
            translation="У Франції вечеряють рано.",
            options=("se", "lo"),
            answer="se",
            note="Безособове se плюс третя особа: se cena.",
        ),
        Exercise(
            id="e3",
            sentence="Se ___ habitaciones para estudiantes.",
            translation="Здаються кімнати для студентів.",
            options=("alquila", "alquilan"),
            answer="alquilan",
            note="Habitaciones у множині, тому alquilan.",
        ),
        Exercise(
            id="e4",
            sentence="___ cayó el teléfono.",
            translation="У мене впав телефон (випадково).",
            options=("Se me", "Me se"),
            answer="Se me",
            note="Випадково, не навмисно: se me cayó.",
        ),
        Exercise(
            id="e5",
            sentence="En esta oficina no ___ fumar.",
            translation="У цьому офісі не можна курити.",
            options=("se puede", "se pueden"),
            answer="se puede",
            note="Далі йде інфінітив, тому дієслово в однині: se puede.",
        ),
        Exercise(
            id="e6",
            sentence="Se ___ (hablar) varios idiomas en Suiza.",
            translation="У Швейцарії говорять кількома мовами.",
            options=(),
            answer="hablan",
            note="Idiomas у множині, тому hablan.",
        ),
    ),
)
