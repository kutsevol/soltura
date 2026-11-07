from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="conditional",
    level="B1",
    order=30,
    title="Умовний спосіб: hablaría",
    lesson=Lesson(
        points=(
            "Утворення: інфінітив плюс -ía, -ías, -ía, -íamos, -íais, -ían: hablaría, comerías, viviría. Закінчення однакові для всіх дієслів.",
            "Деякі дієслова мають змінену основу, як і в майбутньому часі: tener — tendría, hacer — haría, decir — diría, poder — podría, querer — querría, saber — sabría, salir — saldría, venir — vendría, poner — pondría.",
            "Для ввічливих прохань і порад: ¿podría decirme la hora? Me gustaría un café. Yo en tu lugar no lo haría.",
            "Для гіпотез: con más dinero, tendría una casa más grande. Sería mejor salir ya.",
        ),
        examples=(
            Example(
                spanish="¿Podrías abrir la ventana?", ukrainian="Чи не міг би ти відчинити вікно?"
            ),
            Example(
                spanish="Me gustaría un café con leche.", ukrainian="Я б хотів каву з молоком."
            ),
            Example(
                spanish="Yo en tu lugar hablaría con él.",
                ukrainian="На твоєму місці я б поговорив з ним.",
            ),
            Example(
                spanish="Con más tiempo, viajaría más.",
                ukrainian="Якби було більше часу, я б більше подорожував.",
            ),
            Example(spanish="Sería mejor salir ya.", ukrainian="Було б краще вийти вже зараз."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Con un buen sueldo, yo ___ un coche nuevo.",
            translation="З хорошою зарплатою я мав би нову машину.",
            options=("tendría", "tenería"),
            answer="tendría",
            note="Tener має змінену основу tendr-: tendría.",
        ),
        Exercise(
            id="e2",
            sentence="En tu lugar, yo ___ más temprano.",
            translation="На твоєму місці я б вийшов раніше.",
            options=("saldría", "saliría"),
            answer="saldría",
            note="Salir має змінену основу saldr-: saldría.",
        ),
        Exercise(
            id="e3",
            sentence="¿___ decirme dónde está la estación?",
            translation="Чи не могли б ви сказати, де станція?",
            options=("Podría", "Pudo"),
            answer="Podría",
            note="Ввічливе прохання — умовний спосіб: podría.",
        ),
        Exercise(
            id="e4",
            sentence="Con más tiempo, nosotros ___ al cine más a menudo.",
            translation="Якби в нас було більше часу, ми б ходили в кіно частіше.",
            options=("iríamos", "fuimos"),
            answer="iríamos",
            note="Гіпотеза — умовний спосіб: iríamos.",
        ),
        Exercise(
            id="e5",
            sentence="¿___ (venir, tú, condicional) conmigo al cine?",
            translation="Ти б пішов зі мною в кіно?",
            options=(),
            answer="vendrías",
            note="Venir має змінену основу vendr-: vendrías.",
        ),
        Exercise(
            id="e6",
            sentence="Yo ___ (decir, condicional) la verdad.",
            translation="Я б сказав правду.",
            options=(),
            answer="diría",
            note="Decir має змінену основу dir-: diría.",
        ),
    ),
)
