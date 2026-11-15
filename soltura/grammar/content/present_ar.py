from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="present_ar",
    level="A1",
    order=34,
    title="Теперішній час: дієслова на -ar",
    lesson=Lesson(
        points=(
            "Теперішній час (presente) каже, що відбувається зараз і що є постійно: estudio español — я вивчаю іспанську; trabajo en un banco — я працюю в банку. Українською так само, одна форма.",
            "Правильні дієслова на -ar міняють закінчення: відкидаємо -ar і додаємо -o, -as, -a, -amos, -áis, -an. Hablar: (yo) hablo, (tú) hablas, (él, ella, usted) habla, (nosotros) hablamos, (vosotros) habláis, (ellos, ustedes) hablan.",
            "У дієсловах на -ar наголос на письмі є лише у формі habláis. Форма habla — це і «він», і «вона», і «Ви»: хто саме, видно з контексту або з займенника: ella habla.",
            "Часті правильні дієслова на -ar: hablar (говорити), trabajar (працювати), estudiar (вчити, вчитися), comprar (купувати), cenar (вечеряти), cocinar (готувати), viajar (подорожувати), escuchar (слухати), bailar (танцювати).",
            "Заперечення no стоїть перед дієсловом: no hablo inglés, no trabajamos hoy.",
            "Не всі дієслова на -ar змінюються так просто (pensar — pienso, jugar — juego): їх вивчимо пізніше.",
        ),
        examples=(
            Example(
                spanish="Hablo español y un poco de inglés.",
                ukrainian="Я розмовляю іспанською і трохи англійською.",
            ),
            Example(spanish="Trabajas en un banco.", ukrainian="Ти працюєш у банку."),
            Example(spanish="Mi madre cocina muy bien.", ukrainian="Моя мама дуже добре готує."),
            Example(
                spanish="Estudiamos español en la escuela.",
                ukrainian="Ми вивчаємо іспанську в школі.",
            ),
            Example(spanish="¿Cenáis en casa?", ukrainian="Ви вечеряєте вдома?"),
            Example(
                spanish="Mis amigos bailan en la fiesta.",
                ukrainian="Мої друзі танцюють на вечірці.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Yo ___ español en casa.",
            translation="Я розмовляю іспанською вдома.",
            options=("hablo", "hablas"),
            answer="hablo",
            note="Yo: закінчення -o.",
        ),
        Exercise(
            id="e2",
            sentence="Tú ___ en una tienda.",
            translation="Ти працюєш у магазині.",
            options=("trabajas", "trabaja"),
            answer="trabajas",
            note="Tú: закінчення -as.",
        ),
        Exercise(
            id="e3",
            sentence="Nosotros ___ en casa.",
            translation="Ми вечеряємо вдома.",
            options=("cenamos", "cenáis"),
            answer="cenamos",
            note="Nosotros: закінчення -amos.",
        ),
        Exercise(
            id="e4",
            sentence="Mis padres ___ mucho.",
            translation="Мої батьки багато подорожують.",
            options=("viajan", "viaja"),
            answer="viajan",
            note="Mis padres — це «вони»: закінчення -an.",
        ),
        Exercise(
            id="e5",
            sentence="Vosotros ___ (estudiar) español.",
            translation="Ви вивчаєте іспанську.",
            options=(),
            answer="estudiáis",
            note="Vosotros: закінчення -áis, з наголосом.",
        ),
        Exercise(
            id="e6",
            sentence="Ella ___ (comprar) pan.",
            translation="Вона купує хліб.",
            options=(),
            answer="compra",
            note="Ella: закінчення -a.",
        ),
    ),
)
