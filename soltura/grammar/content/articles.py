from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="articles",
    level="A2",
    order=10,
    title="Артикль: el, la, un, una чи без артикля",
    lesson=Lesson(
        points=(
            "Означений артикль (el, la, los, las) стоїть, коли обидва знають, про що мова: el libro que compré. Неозначений (un, una, unos, unas) — коли річ нова або одна з багатьох: compré un libro.",
            "Після hay зазвичай стоїть неозначений артикль, числівник або жодного артикля, а не el: hay un parque, hay parques.",
            "Після ser професія й національність зазвичай без артикля: soy médica, es ucraniano. Якщо людину оцінюють (bueno, excelente), додаємо un чи una: es una médica excelente.",
            "Мову після hablar, estudiar, aprender зазвичай називаємо без артикля: hablo español. Як підмет мова з артиклем: el español es fácil.",
            "Los lunes — щопонеділка; el lunes — якийсь один конкретний понеділок.",
            "Перед жіночим іменником з наголошеним a- стоїть el, а прикметник лишається жіночим: el agua fría, але las aguas.",
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
            sentence="En mi ciudad hay ___ museos muy buenos.",
            translation="У моєму місті є дуже хороші музеї.",
            options=("(без артикля)", "los"),
            answer="(без артикля)",
            note="Після hay зазвичай без артикля: hay museos.",
        ),
        Exercise(
            id="e3",
            sentence="___ lunes trabajo en casa.",
            translation="По понеділках я працюю вдома.",
            options=("el", "los"),
            answer="los",
            note="Los lunes — щопонеділка; el lunes — один конкретний понеділок.",
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
