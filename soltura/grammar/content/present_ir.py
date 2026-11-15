from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="present_ir",
    level="A1",
    order=38,
    title="Дієслово ir: voy, vas, va",
    lesson=Lesson(
        points=(
            "Ir — «йти, їхати». Це одне з найчастіших дієслів, і воно відмінюється неправильно: (yo) voy, (tú) vas, (él, ella, usted) va, (nosotros) vamos, (vosotros) vais, (ellos, ustedes) van.",
            "Куди йдемо: ir a + місце. Voy a Madrid, vas a casa, va a la playa. Після a перед чоловічим іменником з el отримуємо al: voy al cine, va al banco.",
            "Як їдемо: ir en + транспорт — voy en tren, vamos en coche, van en autobús. Пішки — a pie: voy a pie.",
            "Питаємо «куди?» словом adónde (пишуть і a dónde): ¿Adónde vas? — Куди ти йдеш? ¿Adónde va usted? — Куди Ви йдете?",
            "Voy a + місце — це «куди»; voy a + інфінітив — це «що збираюся робити» (voy a comer; тут a — не прийменник місця). Це окрема тема, ми дійдемо до неї пізніше.",
        ),
        examples=(
            Example(spanish="Voy a Madrid en tren.", ukrainian="Я їду до Мадрида потягом."),
            Example(spanish="¿Adónde vas?", ukrainian="Куди ти йдеш?"),
            Example(spanish="Mi hermana va al colegio.", ukrainian="Моя сестра йде до школи."),
            Example(spanish="Vamos a casa.", ukrainian="Ми йдемо додому."),
            Example(spanish="Vais a la playa en coche.", ukrainian="Ви їдете на пляж машиною."),
            Example(
                spanish="Mis padres van a pie al mercado.",
                ukrainian="Мої батьки йдуть на ринок пішки.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Yo ___ a Sevilla en coche.",
            translation="Я їду до Севільї машиною.",
            options=("voy", "va"),
            answer="voy",
            note="Yo: voy.",
        ),
        Exercise(
            id="e2",
            sentence="Mi hermano ___ al trabajo.",
            translation="Мій брат іде на роботу.",
            options=("va", "vas"),
            answer="va",
            note="Мій брат — це «він»: va.",
        ),
        Exercise(
            id="e3",
            sentence="Nosotros ___ al parque.",
            translation="Ми йдемо в парк.",
            options=("vamos", "vais"),
            answer="vamos",
            note="Nosotros: vamos.",
        ),
        Exercise(
            id="e4",
            sentence="Voy ___ biblioteca.",
            translation="Я йду до бібліотеки.",
            options=("al", "a la"),
            answer="a la",
            note="Biblioteca — жіночого роду: a la. Al — лише перед чоловічим (a + el).",
        ),
        Exercise(
            id="e5",
            sentence="Vosotros ___ al cine en autobús.",
            translation="Ви їдете до кінотеатру автобусом.",
            options=(),
            answer="vais",
            note="Vosotros: vais, без наголосу.",
        ),
        Exercise(
            id="e6",
            sentence="Mis tíos ___ a la playa en tren.",
            translation="Мої дядько й тітка їдуть на пляж потягом.",
            options=(),
            answer="van",
            note="Вони: van.",
        ),
    ),
)
