from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="si_clauses",
    level="B1",
    order=100,
    title="Умовні речення з si",
    lesson=Lesson(
        points=(
            "Реальна, можлива умова: si + теперішній час, далі теперішній або майбутній: si llueve, me quedo en casa; si tengo tiempo, iré.",
            "Малоймовірна чи нереальна умова: si + imperfecto de subjuntivo, далі умовний спосіб: si tuviera dinero, viajaría — якби в мене були гроші, я б подорожував.",
            "Imperfecto de subjuntivo: беремо форму ellos від indefinido, відкидаємо -ron і додаємо -ra, -ras, -ra, -ramos, -rais, -ran; у формі nosotros наголос стоїть на попередній голосній: tuviéramos, habláramos. Приклади: tuvieron — tuviera, hablaron — hablara, fueron — fuera. Є й форма на -se (tuviese), вона теж правильна.",
            "Після si в значенні «якщо, якби» умовний спосіб не ставимо: не si tendría, а si tuviera. Але в непрямому питанні si означає «чи», і там умовний можливий: me preguntó si vendría.",
            "Si fuera tú... — «на твоєму місці»: si fuera tú, hablaría con ella.",
        ),
        examples=(
            Example(
                spanish="Si llueve, me quedo en casa.", ukrainian="Якщо піде дощ, я залишусь удома."
            ),
            Example(
                spanish="Si tengo tiempo, iré al gimnasio.",
                ukrainian="Якщо буде час, піду в спортзал.",
            ),
            Example(
                spanish="Si tuviera más dinero, viajaría más.",
                ukrainian="Якби в мене було більше грошей, я б більше подорожував.",
            ),
            Example(
                spanish="Si fuera tú, hablaría con ella.",
                ukrainian="На твоєму місці я б поговорив з нею.",
            ),
            Example(
                spanish="Si hablaras más despacio, te entendería.",
                ukrainian="Якби ти говорив повільніше, я б тебе розумів.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Si ___ mañana, no iremos a la playa.",
            translation="Якщо завтра піде дощ, ми не поїдемо на пляж.",
            options=("llueve", "lloviera"),
            answer="llueve",
            note="Умова можлива, а головне речення в майбутньому: si + теперішній.",
        ),
        Exercise(
            id="e2",
            sentence="Si ___ más tiempo, aprendería otro idioma.",
            translation="Якби в мене було більше часу, я б вивчив іншу мову.",
            options=("tuviera", "tendría"),
            answer="tuviera",
            note="Після si ставимо imperfecto de subjuntivo: tuviera.",
        ),
        Exercise(
            id="e3",
            sentence="Si yo ___ tú, no lo haría.",
            translation="На твоєму місці я б цього не робив.",
            options=("fuera", "era"),
            answer="fuera",
            note="Після si ставимо imperfecto de subjuntivo: fuera.",
        ),
        Exercise(
            id="e4",
            sentence="Si ___, te ayudaría con la mudanza.",
            translation="Якби я міг, допоміг би тобі з переїздом.",
            options=("pudiera", "podría"),
            answer="pudiera",
            note="Після si ставимо imperfecto de subjuntivo: pudiera.",
        ),
        Exercise(
            id="e5",
            sentence="Si ___ (llover) el sábado, nos quedamos en casa.",
            translation="Якщо в суботу піде дощ, ми залишимось удома.",
            options=(),
            answer="llueve",
            note="Умова можлива: si + теперішній час, llueve.",
        ),
        Exercise(
            id="e6",
            sentence="Si ___ menos azúcar, te sentirías mejor.",
            translation="Якби ти їв менше цукру, ти почувався б краще.",
            options=("comieras", "comerías"),
            answer="comieras",
            note="Після si ставимо imperfecto de subjuntivo: comieras.",
        ),
    ),
)
