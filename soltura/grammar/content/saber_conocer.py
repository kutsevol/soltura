from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="saber_conocer",
    level="A2",
    order=105,
    title="saber чи conocer: знати",
    lesson=Lesson(
        points=(
            "Saber — знати факт або вміти щось робити: sé la respuesta, sé nadar. Saber + інфінітив означає «вміти».",
            "Conocer — бути знайомим з людиною, місцем чи річчю: conozco a Ana, conozco Valencia.",
            "Перед конкретною людиною після conocer ставимо особове a: conozco a tu hermano.",
            "Форми yo неправильні: sé (saber), conozco (conocer).",
            "У pretérito indefinido conocer означає «познайомитися»: ayer conocí a tu madre. В imperfecto — «знати»: conocía a tu madre.",
        ),
        examples=(
            Example(spanish="Sé la dirección de la oficina.", ukrainian="Я знаю адресу офісу."),
            Example(spanish="Sé cocinar muy bien.", ukrainian="Я вмію дуже добре готувати."),
            Example(spanish="Conozco a tu hermano.", ukrainian="Я знаю твого брата."),
            Example(spanish="¿Conoces Barcelona?", ukrainian="Ти знаєш Барселону?"),
            Example(
                spanish="Ayer conocí a tu madre.", ukrainian="Вчора я познайомився з твоєю мамою."
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="___ dónde vive Marta.",
            translation="Я знаю, де живе Марта.",
            options=("Sé", "Conozco"),
            answer="Sé",
            note="Знання факту (де вона живе) — saber.",
        ),
        Exercise(
            id="e2",
            sentence="¿___ a mi jefe?",
            translation="Ти знаєш мого начальника?",
            options=("Conoces", "Sabes"),
            answer="Conoces",
            note="Знайомство з людиною — conocer.",
        ),
        Exercise(
            id="e3",
            sentence="Mi hijo ___ nadar desde los cuatro años.",
            translation="Мій син уміє плавати з чотирьох років.",
            options=("sabe", "conoce"),
            answer="sabe",
            note="Уміння — saber + інфінітив.",
        ),
        Exercise(
            id="e4",
            sentence="No ___ esta ciudad; es la primera vez.",
            translation="Я не знаю цього міста: я тут уперше.",
            options=("conozco", "sé"),
            answer="conozco",
            note="Знайомство з місцем — conocer.",
        ),
        Exercise(
            id="e5",
            sentence="Ella no ___ conducir.",
            translation="Вона не вміє водити.",
            options=("sabe", "conoce"),
            answer="sabe",
            note="Уміння — saber + інфінітив.",
        ),
        Exercise(
            id="e6",
            sentence="El año pasado ___ a mi marido en Valencia.",
            translation="Минулого року я познайомилася з чоловіком у Валенсії.",
            options=("conocí", "conozco"),
            answer="conocí",
            note="У минулому (el año pasado) conocer означає «познайомитися»: conocí.",
        ),
    ),
)
