from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="ir_a_infinitive",
    level="A2",
    order=42,
    title="ir a + інфінітив: найближчі плани",
    lesson=Lesson(
        points=(
            "Voy a + інфінітив — найпростіший спосіб сказати про майбутнє в розмові: voy a comer — я збираюся поїсти, зараз поїм.",
            "Ir змінюється за особами: voy, vas, va, vamos, vais, van. Далі завжди a, потім інфінітив, який не змінюється.",
            "Так говорять про близькі плани й наміри: mañana voy a trabajar en casa.",
            "Не плутайте з ir a + місце: voy a Madrid — їду до Мадрида; voy a comer — збираюся їсти.",
            "Заперечення no стоїть перед ir: no voy a comer.",
        ),
        examples=(
            Example(spanish="Voy a llamar a mi madre.", ukrainian="Зателефоную мамі."),
            Example(spanish="¿Qué vas a hacer el sábado?", ukrainian="Що ти робитимеш у суботу?"),
            Example(
                spanish="Mis amigos van a venir a cenar.", ukrainian="Мої друзі прийдуть на вечерю."
            ),
            Example(spanish="No vamos a llegar a tiempo.", ukrainian="Ми не встигнемо."),
            Example(spanish="Voy a Madrid en tren.", ukrainian="Я їду до Мадрида потягом."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Yo ___ a cocinar esta noche.",
            translation="Сьогодні ввечері я готуватиму.",
            options=("voy", "va"),
            answer="voy",
            note="Підмет yo, тому voy.",
        ),
        Exercise(
            id="e2",
            sentence="Mis padres ___ a viajar en agosto.",
            translation="Мої батьки поїдуть у серпні.",
            options=("van", "vamos"),
            answer="van",
            note="Mis padres — вони, тому van.",
        ),
        Exercise(
            id="e3",
            sentence="Voy a ___ una película esta noche.",
            translation="Сьогодні ввечері подивлюся фільм.",
            options=("ver", "veo"),
            answer="ver",
            note="Після voy a стоїть інфінітив, який не змінюється: ver.",
        ),
        Exercise(
            id="e4",
            sentence="¿A qué hora ___ a salir tú?",
            translation="О котрій ти вийдеш?",
            options=("vas", "vais"),
            answer="vas",
            note="Підмет tú, тому vas.",
        ),
        Exercise(
            id="e5",
            sentence="Nosotros ___ a comprar pan.",
            translation="Ми купимо хліб.",
            options=("vamos", "vais"),
            answer="vamos",
            note="Підмет nosotros, тому vamos.",
        ),
        Exercise(
            id="e6",
            sentence="Ella no ___ a llegar tarde.",
            translation="Вона не спізниться.",
            options=("va", "vas"),
            answer="va",
            note="Підмет ella, тому va; no стоїть перед ir.",
        ),
    ),
)
