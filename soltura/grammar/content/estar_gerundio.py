from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="estar_gerundio",
    level="A2",
    order=52,
    title="estar + герундій: що відбувається зараз",
    lesson=Lesson(
        points=(
            "Estoy comiendo — дія відбувається саме зараз. Це estar + герундій.",
            "Герундій: -ar → -ando (hablar → hablando); -er і -ir → -iendo (comer → comiendo, vivir → viviendo).",
            "Деякі герундії неправильні: leer → leyendo, dormir → durmiendo, pedir → pidiendo.",
            "Герундій не змінюється, змінюється лише estar: estoy, estás, está, estamos, estáis, están.",
            "Для звичок і регулярних дій зазвичай вживаємо просто теперішній час: trabajo en una oficina. Estoy trabajando en casa hoy — сьогодні, тимчасово.",
        ),
        examples=(
            Example(spanish="Estoy comiendo.", ukrainian="Я зараз їм."),
            Example(spanish="Mis hijos están durmiendo.", ukrainian="Мої діти сплять."),
            Example(spanish="¿Qué estás leyendo?", ukrainian="Що ти читаєш?"),
            Example(spanish="Estamos esperando el autobús.", ukrainian="Ми чекаємо на автобус."),
            Example(spanish="Trabajo en una oficina.", ukrainian="Я працюю в офісі."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Todos los días ___ en una oficina del centro.",
            translation="Щодня я працюю в офісі в центрі.",
            options=("trabajo", "estoy trabajando"),
            answer="trabajo",
            note="Регулярна, звична дія — це зазвичай просто теперішній час.",
        ),
        Exercise(
            id="e2",
            sentence="Mis padres ___ viendo la tele.",
            translation="Мої батьки дивляться телевізор.",
            options=("están", "estamos"),
            answer="están",
            note="Mis padres — вони, тому están.",
        ),
        Exercise(
            id="e3",
            sentence="Ahora estoy ___ un libro muy largo.",
            translation="Зараз я читаю дуже довгу книжку.",
            options=("leyendo", "leiendo"),
            answer="leyendo",
            note="У leer між двома голосними i стає y: leyendo.",
        ),
        Exercise(
            id="e4",
            sentence="Estamos ___ la cuenta.",
            translation="Ми просимо рахунок.",
            options=("pidiendo", "pediendo"),
            answer="pidiendo",
            note="У pedir голосна e змінюється на i: pidiendo.",
        ),
        Exercise(
            id="e5",
            sentence="El bebé está ___ (dormir) en su cuarto.",
            translation="Малюк спить у своїй кімнаті.",
            options=(),
            answer="durmiendo",
            note="Dormir має герундій durmiendo: o змінюється на u.",
        ),
        Exercise(
            id="e6",
            sentence="Ahora mismo estoy ___ (estudiar) español.",
            translation="Саме зараз я вчу іспанську.",
            options=(),
            answer="estudiando",
            note="Дієслова на -ar мають герундій на -ando: estudiando.",
        ),
    ),
)
