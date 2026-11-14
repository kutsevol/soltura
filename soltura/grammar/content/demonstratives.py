from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="demonstratives",
    level="A1",
    order=70,
    title="este, ese, aquel: цей, той, он той",
    lesson=Lesson(
        points=(
            "В Іспанії розрізняють три ступені: este, esta — близько до мене; ese, esa — близько до співрозмовника; aquel, aquella — далеко від обох. У багатьох країнах Латинської Америки ese означає і далекий предмет, а aquel рідкісне.",
            "Вони узгоджуються: este libro, esta casa, estos libros, estas casas; ese, esa, esos, esas; aquel, aquella, aquellos, aquellas.",
            "Коли іменник пропущено, але відомо, про що мова, кажемо este, esta, ese: esta es mi hermana. Esto, eso, aquello — коли не знаємо, що це, або про цілу ситуацію: ¿qué es esto?, eso es verdad.",
            "З часом: este año, esta semana, esta noche — цього року, цього тижня, сьогодні ввечері.",
        ),
        examples=(
            Example(spanish="Este libro es mío.", ukrainian="Ця книжка моя."),
            Example(spanish="¿Me das esa botella?", ukrainian="Даси мені ту пляшку (біля тебе)?"),
            Example(
                spanish="Aquella montaña es muy alta.", ukrainian="Та гора (далеко) дуже висока."
            ),
            Example(spanish="¿Qué es esto?", ukrainian="Що це?"),
            Example(spanish="Esta noche voy al cine.", ukrainian="Сьогодні ввечері йду в кіно."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="___ piso es muy grande.",
            translation="Ця квартира дуже велика.",
            options=("este", "esta"),
            answer="este",
            note="Piso чоловічого роду, хоч «квартира» в українській жіночого: este piso.",
        ),
        Exercise(
            id="e2",
            sentence="___ libros son de mi hermana.",
            translation="Ці книжки моєї сестри.",
            options=("estos", "estas"),
            answer="estos",
            note="Libros чоловічого роду в множині: estos libros.",
        ),
        Exercise(
            id="e3",
            sentence="Esta casa es mía, esa es de mi vecino y ___ de allá, al fondo, es de mis padres.",
            translation="Цей будинок мій, той — мого сусіда, а он той, далеко в глибині, — моїх батьків.",
            options=("esa", "aquella"),
            answer="aquella",
            note="В Іспанії найдалі від обох — aquella.",
        ),
        Exercise(
            id="e4",
            sentence="___ es verdad.",
            translation="Це правда.",
            options=("eso", "ese"),
            answer="eso",
            note="Про цілу ситуацію без іменника кажемо eso.",
        ),
        Exercise(
            id="e5",
            sentence="___ año voy a estudiar más.",
            translation="Цього року буду вчитися більше.",
            options=("este", "esta"),
            answer="este",
            note="Año чоловічого роду: este año.",
        ),
        Exercise(
            id="e6",
            sentence="¿Me das ___ botella que tienes ahí?",
            translation="Даси мені ту пляшку, що в тебе там?",
            options=("esta", "esa"),
            answer="esa",
            note="Пляшка біля співрозмовника (ahí) — esa.",
        ),
    ),
)
