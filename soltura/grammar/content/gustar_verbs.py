from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="gustar_verbs",
    level="A2",
    order=80,
    title="gustar: мені подобається",
    lesson=Lesson(
        points=(
            "Gustar значить «подобатися»: подобається те, що є підметом, а людина стоїть у непрямому додатку: me gusta el café — мені подобається кава.",
            "Me, te, le, nos, os, les показують, кому подобається. Gusta чи gustan узгоджується з тим, що подобається: me gusta el libro, me gustan los libros.",
            "Коли подобається дія і далі йде інфінітив, завжди gusta: me gusta leer, me gusta leer y escribir.",
            "Так само працюють encantar (дуже подобатися), interesar, doler: me encanta Madrid, me duelen los pies.",
            "Хто саме — додаємо a mí, a ti, a él, a nosotros або ім’я, але me, te, le, nos, os, les залишаються обов’язковими: a Juan le gusta el fútbol.",
        ),
        examples=(
            Example(spanish="Me gusta el café.", ukrainian="Мені подобається кава."),
            Example(
                spanish="No me gustan las películas de miedo.",
                ukrainian="Мені не подобаються фільми жахів.",
            ),
            Example(spanish="¿Te gusta bailar?", ukrainian="Тобі подобається танцювати?"),
            Example(
                spanish="A mi madre le encanta cocinar.", ukrainian="Моя мама обожнює готувати."
            ),
            Example(spanish="Nos gustan los museos.", ukrainian="Нам подобаються музеї."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Me ___ las naranjas.",
            translation="Мені подобаються апельсини.",
            options=("gusta", "gustan"),
            answer="gustan",
            note="Naranjas у множині, тому gustan.",
        ),
        Exercise(
            id="e2",
            sentence="Me ___ viajar en tren.",
            translation="Мені подобається їздити потягом.",
            options=("gusta", "gustan"),
            answer="gusta",
            note="Коли далі йде інфінітив, завжди gusta.",
        ),
        Exercise(
            id="e3",
            sentence="A mi hermano ___ gusta el fútbol.",
            translation="Моєму братові подобається футбол.",
            options=("me", "le"),
            answer="le",
            note="A mi hermano — він, тому le.",
        ),
        Exercise(
            id="e4",
            sentence="¿___ gusta el pescado?",
            translation="Тобі подобається риба?",
            options=("te", "tú"),
            answer="te",
            note="Займенник перед gusta — te, не tú.",
        ),
        Exercise(
            id="e5",
            sentence="A nosotros ___ encantan las playas.",
            translation="Нам дуже подобаються пляжі.",
            options=(),
            answer="nos",
            note="A nosotros — нам, тому nos.",
        ),
        Exercise(
            id="e6",
            sentence="Me ___ la cabeza.",
            translation="У мене болить голова.",
            options=(),
            answer="duele",
            note="Doler працює як gustar: болить одна голова (la cabeza), тому duele.",
        ),
    ),
)
