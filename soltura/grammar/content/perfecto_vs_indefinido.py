from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="perfecto_vs_indefinido",
    level="B1",
    order=20,
    title="perfecto чи indefinido",
    lesson=Lesson(
        points=(
            "Про час, що ще триває (hoy, esta semana, este año, últimamente), в Іспанії зазвичай кажуть perfecto: hoy he comido pizza.",
            "Про час, що вже закінчився (ayer, anoche, la semana pasada, el año pasado, en 2020), кажуть indefinido: ayer comí pizza.",
            "Про досвід без точного часу в Іспанії зазвичай perfecto, якщо період ще не закрито: ¿has estado en Madrid? Про людину чи період, що минули, — indefinido: mi abuelo nunca viajó en avión. Коли називаємо точний час, теж indefinido: estuve en Madrid en 2020.",
            "В Іспанії ya і todavía no зазвичай стоять з perfecto: ya he comido, todavía no he comido. З закінченим часом лишається indefinido: ya te lo dije ayer.",
            "У більшості країн Америки, а також у Галісії, Астурії та на Канарах частіше кажуть indefinido і про сьогодні: hoy comí.",
        ),
        examples=(
            Example(spanish="Hoy he comido muy pronto.", ukrainian="Сьогодні я поїв дуже рано."),
            Example(spanish="Ayer comí a las tres.", ukrainian="Вчора я їв о третій."),
            Example(
                spanish="Este año he viajado mucho.", ukrainian="Цього року я багато подорожував."
            ),
            Example(
                spanish="El año pasado viajé a Italia.",
                ukrainian="Минулого року я їздив до Італії.",
            ),
            Example(spanish="¿Has probado la paella?", ukrainian="Ти куштував паелью?"),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Esta mañana ___ mucho.",
            translation="Сьогодні вранці я багато працював.",
            options=("he trabajado", "trabajé"),
            answer="he trabajado",
            note="День ще не скінчився: в Іспанії зазвичай perfecto (indefinido теж трапляється в Галісії й Америці).",
        ),
        Exercise(
            id="e2",
            sentence="El año pasado ___ a Galicia de vacaciones.",
            translation="Минулого року ми їздили у відпустку до Галісії.",
            options=("fuimos", "hemos ido"),
            answer="fuimos",
            note="El año pasado вже закінчився, тому indefinido.",
        ),
        Exercise(
            id="e3",
            sentence="¿___ alguna vez esta serie?",
            translation="Ти колись бачив цей серіал?",
            options=("Has visto", "Viste"),
            answer="Has visto",
            note="В Іспанії про досвід зазвичай perfecto; в Латинській Америці природніше «¿Viste alguna vez…?».",
        ),
        Exercise(
            id="e4",
            sentence="Mi hermano me ___ anoche.",
            translation="Мій брат зателефонував мені вчора ввечері.",
            options=("llamó", "ha llamado"),
            answer="llamó",
            note="Anoche вже минуло, тому indefinido.",
        ),
        Exercise(
            id="e5",
            sentence="Todavía no ___ los invitados.",
            translation="Гості ще не приїхали.",
            options=("han llegado", "llegaron"),
            answer="han llegado",
            note="В Іспанії todavía no зазвичай стоїть з perfecto.",
        ),
        Exercise(
            id="e6",
            sentence="En 2019 ___ en Sevilla.",
            translation="У 2019 році я жив у Севільї.",
            options=("viví", "he vivido"),
            answer="viví",
            note="З точним роком, що минув, indefinido.",
        ),
    ),
)
