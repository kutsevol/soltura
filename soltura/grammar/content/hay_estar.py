from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="hay_estar",
    level="A1",
    order=50,
    title="hay чи está",
    lesson=Lesson(
        points=(
            "Hay каже, що щось є, існує: hay un banco cerca, hay dos parques. Це щось нове, невизначене.",
            "Hay не змінюється за числом: hay un libro, hay tres libros.",
            "Estar каже, де знаходиться відоме, конкретне: el banco está en la esquina, mis llaves están en la mesa.",
            "Після hay: un, una, числівник, muchos, algunos або без артикля. Перед estar: el, la, присвійне (mi, tu), вказівне (este, ese) або ім’я.",
            "Питання «чи є взагалі?» — ¿Hay un banco por aquí? Питання «де саме?» — ¿Dónde está el banco?",
        ),
        examples=(
            Example(
                spanish="Hay un supermercado cerca de mi casa.",
                ukrainian="Біля мого дому є супермаркет.",
            ),
            Example(
                spanish="El supermercado está en la calle Colón.",
                ukrainian="Супермаркет на вулиці Колон.",
            ),
            Example(spanish="¿Hay una farmacia por aquí?", ukrainian="Тут є аптека?"),
            Example(spanish="¿Dónde está la farmacia?", ukrainian="Де аптека?"),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="___ un banco en esta calle.",
            translation="На цій вулиці є банк.",
            options=("hay", "está"),
            answer="hay",
            note="Новий, невизначений банк (un banco) — hay.",
        ),
        Exercise(
            id="e2",
            sentence="El banco ___ en la esquina.",
            translation="Банк на розі.",
            options=("hay", "está"),
            answer="está",
            note="Конкретний банк (el banco) — estar.",
        ),
        Exercise(
            id="e3",
            sentence="En mi clase ___ veinte alumnos.",
            translation="У моєму класі двадцять учнів.",
            options=("hay", "están"),
            answer="hay",
            note="Hay не змінюється і з числівником.",
        ),
        Exercise(
            id="e4",
            sentence="Mis llaves ___ en la mesa.",
            translation="Мої ключі на столі.",
            options=("hay", "están"),
            answer="están",
            note="Мої ключі — конкретна річ, тож estar у множині.",
        ),
        Exercise(
            id="e5",
            sentence="¿___ un banco cerca de aquí?",
            translation="Чи є тут поруч банк?",
            options=(),
            answer="hay",
            note="Питання про те, чи є банк узагалі, — hay.",
        ),
        Exercise(
            id="e6",
            sentence="¿Dónde ___ la estación?",
            translation="Де станція?",
            options=("hay", "está"),
            answer="está",
            note="Питання про конкретну станцію — estar.",
        ),
    ),
)
