from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="personal_a",
    level="A2",
    order=60,
    title="Особове a: veo a María",
    lesson=Lesson(
        points=(
            "Коли прямий додаток — конкретна людина (або тварина, яку ми любимо як людину), перед ним стоїть a: veo a María, llamo a mi madre, quiero a mi perro.",
            "Перед речами a немає: veo la casa, busco mi llave.",
            "Коли tener значить «мати» (родичів, друзів), особове a не ставимо: tengo dos hermanos.",
            "З alguien, nadie, quién особове a зазвичай потрібне: no conozco a nadie, ¿a quién ves? Після hay його немає: no hay nadie.",
            "A + el зливається в al: conozco al nuevo profesor.",
            "Не плутайте з a, що означає напрямок: voy a casa.",
        ),
        examples=(
            Example(spanish="Veo a María en el parque.", ukrainian="Я бачу Марію в парку."),
            Example(
                spanish="Veo el parque desde mi ventana.", ukrainian="Я бачу парк зі свого вікна."
            ),
            Example(spanish="Conozco al nuevo profesor.", ukrainian="Я знаю нового вчителя."),
            Example(spanish="Tengo dos hermanos.", ukrainian="У мене двоє братів."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Llamo ___ mi madre todos los días.",
            translation="Я телефоную мамі щодня.",
            options=("a", "(без a)"),
            answer="a",
            note="Мама — конкретна людина, тому a.",
        ),
        Exercise(
            id="e2",
            sentence="Saludo ___ vecino cada mañana.",
            translation="Я вітаюся із сусідом щоранку.",
            options=("a", "al"),
            answer="al",
            note="A + el зливається в al: al vecino.",
        ),
        Exercise(
            id="e3",
            sentence="Busco ___ mi llave.",
            translation="Я шукаю свій ключ.",
            options=("a", "(без a)"),
            answer="(без a)",
            note="Ключ — річ, тому a не потрібне.",
        ),
        Exercise(
            id="e4",
            sentence="Tengo ___ dos hermanos.",
            translation="У мене двоє братів.",
            options=("a", "(без a)"),
            answer="(без a)",
            note="Коли tener значить «мати» родичів, особове a не ставимо.",
        ),
        Exercise(
            id="e5",
            sentence="No conozco ___ nadie aquí.",
            translation="Тут я нікого не знаю.",
            options=(),
            answer="a",
            note="З nadie особове a зазвичай потрібне.",
        ),
        Exercise(
            id="e6",
            sentence="Quiero mucho ___ mi perro.",
            translation="Я дуже люблю свого пса.",
            options=(),
            answer="a",
            note="Домашню тварину, яку любимо, зазвичай називаємо з a, як людину.",
        ),
    ),
)
