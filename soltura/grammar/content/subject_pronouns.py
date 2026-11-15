from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="subject_pronouns",
    level="A1",
    order=32,
    title="Особові займенники: yo, tú, él",
    lesson=Lesson(
        points=(
            "Особові займенники-підмети: yo (я), tú (ти), él (він), ella (вона), nosotros / nosotras (ми), vosotros / vosotras (ви, кілька людей, кожному з яких кажемо «ти»), ellos / ellas (вони). Форми на -as — коли всі жінки; якщо серед людей є хоч один чоловік, кажемо nosotros, vosotros, ellos.",
            "Él з наголосом — це «він», а el без наголосу — означений артикль: él es mi padre, el padre es alto.",
            "Ввічливе «Ви» — usted (до однієї людини) і ustedes (до кількох): так звертаємося до незнайомих людей і в офіційній розмові. Дієслово при них стоїть у формі «він» і «вони»: usted habla, ustedes hablan. У більшій частині Іспанії vosotros — «ви» до друзів і рідних, а ustedes — ввічливе. У Латинській Америці та на Канарських островах ustedes кажуть і друзям.",
            "Займенник-підмет зазвичай пропускаємо: закінчення дієслова вже каже, хто діє. Кажемо hablo español. Yo hablo español теж правильно, але звучить як підкреслення («саме я»). Українською «я» ставимо майже завжди, а іспанською — ні. Форми дієслів у прикладах вивчимо в наступних уроках, а зараз дивіться на займенники.",
            "Ставимо займенник, коли протиставляємо людей або підкреслюємо, хто саме: Yo soy Clara, ¿y tú? — ¿Quién habla español? — Yo.",
            "Про речі особовий займенник зазвичай не вживаємо: не ella es grande, а просто es grande.",
        ),
        examples=(
            Example(spanish="Yo soy Clara, ¿y tú?", ukrainian="Я Клара, а ти?"),
            Example(spanish="Vivo en Madrid.", ukrainian="Я живу в Мадриді."),
            Example(spanish="Nosotras somos amigas.", ukrainian="Ми подруги."),
            Example(spanish="¿Usted habla inglés?", ukrainian="Ви говорите англійською?"),
            Example(
                spanish="Pedro y Ana trabajan aquí. Ellos son hermanos.",
                ukrainian="Педро й Ана працюють тут. Вони брат і сестра.",
            ),
            Example(spanish="Tengo un coche. Es rojo.", ukrainian="У мене є машина. Вона червона."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Pedro y Ana son mis amigos. ___ viven en Madrid.",
            translation="Педро й Ана — мої друзі. Вони живуть у Мадриді.",
            options=("Ellos", "Ellas"),
            answer="Ellos",
            note="Серед людей є чоловік (Pedro), тож ellos.",
        ),
        Exercise(
            id="e2",
            sentence="María y Lucía son hermanas. ___ trabajan en un hospital.",
            translation="Марія й Лусія — сестри. Вони працюють у лікарні.",
            options=("Ellos", "Ellas"),
            answer="Ellas",
            note="Обидві — жінки, тож ellas.",
        ),
        Exercise(
            id="e3",
            sentence="Perdone, señora García, ¿___ habla inglés?",
            translation="Вибачте, пані Гарсія, Ви говорите англійською?",
            options=("tú", "usted"),
            answer="usted",
            note="Пані Гарсіа звертаємось на «Ви»: usted. Habla — форма «вона», з tú було б hablas.",
        ),
        Exercise(
            id="e4",
            sentence="___ es mi padre.",
            translation="Він мій батько.",
            options=("Él", "El"),
            answer="Él",
            note="«Він» пишемо з наголосом: él. El без наголосу — артикль.",
        ),
        Exercise(
            id="e5",
            sentence="Tengo una casa. ___ muy grande.",
            translation="У мене є будинок. Він дуже великий.",
            options=("Es", "Ella es"),
            answer="Es",
            note="Про річ займенник не ставимо: просто es, а не ella es.",
        ),
        Exercise(
            id="e6",
            sentence="Yo soy Clara, ¿y ___?",
            translation="Я Клара, а ти?",
            options=(),
            answer="tú",
            note="Звертаємося до друга на «ти»: tú.",
        ),
    ),
)
