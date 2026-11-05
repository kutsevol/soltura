from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="articles",
    level="A2",
    order=10,
    title="Артикль: el, la, un, una чи без артикля",
    lesson=Lesson(
        points=(
            "Означений артикль (el, la, los, las) стоїть, коли обидва знають, про що мова: el libro que compré. Неозначений (un, una, unos, unas) — коли річ нова або одна з багатьох: compré un libro.",
            "Після hay стоїть неозначений артикль, числівник або жодного артикля, ніколи el: hay un parque, hay parques.",
            "Після ser професія й національність зазвичай без артикля: soy médica, es ucraniano. Коли професію описує прикметник після іменника, артикль зазвичай потрібен: es una médica muy buena.",
            "Мову після hablar, estudiar, aprender зазвичай називаємо без артикля: hablo español. Як підмет мова з артиклем: el español es fácil.",
            "Los lunes — щопонеділка; el lunes — у конкретний понеділок, наприклад цього.",
            "Перед жіночим іменником з наголошеним a- стоїть el: el agua fría, але las aguas.",
        ),
        examples=(
            Example(spanish="Soy médica.", ukrainian="Я лікарка."),
            Example(spanish="Es una médica muy buena.", ukrainian="Вона дуже хороша лікарка."),
            Example(
                spanish="Hablo español y estudio inglés.",
                ukrainian="Я говорю іспанською і вчу англійську.",
            ),
            Example(
                spanish="Los lunes trabajo en casa.", ukrainian="По понеділках я працюю вдома."
            ),
            Example(spanish="El agua está fría.", ukrainian="Вода холодна."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Hablo ___ español con mis vecinos.",
            translation="Я говорю іспанською з сусідами.",
            options=("(без артикля)", "el"),
            answer="(без артикля)",
            note="Після hablar мову зазвичай називають без артикля.",
        ),
        Exercise(
            id="e2",
            sentence="Es ___ médica muy buena.",
            translation="Вона дуже хороша лікарка.",
            options=("(без артикля)", "una"),
            answer="una",
            note="Коли професію описує прикметник після іменника, артикль зазвичай потрібен.",
        ),
        Exercise(
            id="e3",
            sentence="___ lunes trabajo en casa.",
            translation="По понеділках я працюю вдома.",
            options=("el", "los"),
            answer="los",
            note="Los lunes означає «щопонеділка»; el lunes — лише цього понеділка.",
        ),
        Exercise(
            id="e4",
            sentence="En mi calle hay ___ supermercado nuevo.",
            translation="На моїй вулиці є новий супермаркет.",
            options=("un", "el"),
            answer="un",
            note="Після hay стоїть неозначений артикль: hay un supermercado.",
        ),
        Exercise(
            id="e5",
            sentence="___ agua está muy fría.",
            translation="Вода дуже холодна.",
            options=("el", "la"),
            answer="el",
            note="Перед жіночим словом з наголошеним a- (agua) стоїть el: el agua.",
        ),
        Exercise(
            id="e6",
            sentence="Compré un libro. ___ libro es muy interesante.",
            translation="Я купив книжку. Книжка дуже цікава.",
            options=("el", "un"),
            answer="el",
            note="Книжку вже згадали, тож означений артикль: el libro.",
        ),
    ),
)
