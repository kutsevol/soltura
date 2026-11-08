from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="subj_doubt_emotion",
    level="B1",
    order=80,
    title="Subjuntivo: сумнів, емоції, оцінка",
    lesson=Lesson(
        points=(
            "Після виразів емоцій і оцінки з que стоїть subjuntivo: me alegro de que vengas, es importante que descanses, es normal que, es una pena que.",
            "Після сумніву й заперечення — також: dudo que, no creo que: no creo que llueva. Після es posible que теж subjuntivo: es posible que llegue tarde. А no dudo que вже з indicativo: no dudo que viene.",
            "Коли є впевненість, стоїть indicativo: creo que viene, estoy seguro de que viene, es verdad que viene.",
            "A lo mejor — «може, можливо» — в Іспанії вживаємо з indicativo: a lo mejor llega tarde.",
            "Коли підмет той самий, кажемо інфінітив: me alegro de estar aquí.",
        ),
        examples=(
            Example(spanish="Me alegro de que vengas.", ukrainian="Я радий, що ти прийдеш."),
            Example(spanish="Es importante que descanses.", ukrainian="Важливо, щоб ти відпочив."),
            Example(
                spanish="No creo que llueva mañana.", ukrainian="Не думаю, що завтра буде дощ."
            ),
            Example(spanish="Creo que llueve mañana.", ukrainian="Думаю, що завтра буде дощ."),
            Example(spanish="A lo mejor llego tarde.", ukrainian="Може, я запізнюсь."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Me alegro de que ___ con nosotros.",
            translation="Я радий, що ти з нами.",
            options=("estés", "estás"),
            answer="estés",
            note="Після me alegro de que стоїть subjuntivo: estés.",
        ),
        Exercise(
            id="e2",
            sentence="Me alegro de ___ aquí contigo.",
            translation="Я радий бути тут з тобою.",
            options=("estar", "estoy"),
            answer="estar",
            note="Підмет той самий, тому інфінітив: me alegro de estar.",
        ),
        Exercise(
            id="e3",
            sentence="No creo que ___ tiempo para todo.",
            translation="Не думаю, що в нас буде час на все.",
            options=("tengamos", "tenemos"),
            answer="tengamos",
            note="Після no creo que стоїть subjuntivo: tengamos.",
        ),
        Exercise(
            id="e4",
            sentence="Creo que mi hermano ___ pronto.",
            translation="Думаю, мій брат скоро прийде.",
            options=("viene", "venga"),
            answer="viene",
            note="Після creo que в ствердженні стоїть indicativo: viene.",
        ),
        Exercise(
            id="e5",
            sentence="A lo mejor ___ mañana mis primos.",
            translation="Може, завтра приїдуть мої двоюрідні брати.",
            options=("vienen", "vengan"),
            answer="vienen",
            note="A lo mejor в Іспанії вживаємо з indicativo: vienen.",
        ),
        Exercise(
            id="e6",
            sentence="Es posible que ella no ___ (poder) venir.",
            translation="Можливо, вона не зможе прийти.",
            options=(),
            answer="pueda",
            note="Після es posible que стоїть subjuntivo: pueda.",
        ),
    ),
)
