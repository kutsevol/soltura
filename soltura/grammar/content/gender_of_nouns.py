from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="gender_of_nouns",
    level="A2",
    order=20,
    title="Рід іменників: el чи la",
    lesson=Lesson(
        points=(
            "В іспанській два роди: чоловічий (el, un) і жіночий (la, una). Середнього роду немає.",
            "Іменники на -o здебільшого чоловічого роду (el libro), на -a жіночого (la casa).",
            "Закінчення -ción, -sión, -dad, -tad, -tud майже завжди жіночого роду: la estación, la ciudad.",
            "Винятки, які треба запам’ятати: el día, el mapa, el problema, el idioma, el tema (чоловічий рід) і la mano, la foto, la moto (жіночий).",
            "Рід не збігається з українським: el coche (машина), la leche (молоко).",
        ),
        examples=(
            Example(spanish="El problema es difícil.", ukrainian="Проблема складна."),
            Example(spanish="La estación está cerca.", ukrainian="Станція близько."),
            Example(
                spanish="Necesito un mapa de la ciudad.", ukrainian="Мені потрібна карта міста."
            ),
            Example(spanish="Me duele la mano.", ukrainian="У мене болить рука."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="___ problema es muy grande.",
            translation="Проблема дуже велика.",
            options=("el", "la"),
            answer="el",
            note="Problema закінчується на -a, але це слово чоловічого роду: el problema.",
        ),
        Exercise(
            id="e2",
            sentence="Voy a ___ estación de autobuses.",
            translation="Я йду на автовокзал.",
            options=("el", "la"),
            answer="la",
            note="Закінчення -ción означає жіночий рід: la estación.",
        ),
        Exercise(
            id="e3",
            sentence="Me duele ___ mano.",
            translation="У мене болить рука.",
            options=("el", "la"),
            answer="la",
            note="Mano закінчується на -o, але жіночого роду: la mano.",
        ),
        Exercise(
            id="e4",
            sentence="Necesito ___ mapa de la ciudad.",
            translation="Мені потрібна карта міста.",
            options=("un", "una"),
            answer="un",
            note="Mapa закінчується на -a, але чоловічого роду: un mapa.",
        ),
        Exercise(
            id="e5",
            sentence="___ leche está en la nevera.",
            translation="Молоко в холодильнику.",
            options=(),
            answer="la",
            note="В українській «молоко» середнього роду, а leche жіночого: la leche.",
        ),
        Exercise(
            id="e6",
            sentence="Hoy es ___ día de mi cumpleaños.",
            translation="Сьогодні день мого народження.",
            options=(),
            answer="el",
            note="Día закінчується на -a, але чоловічого роду: el día.",
        ),
    ),
)
