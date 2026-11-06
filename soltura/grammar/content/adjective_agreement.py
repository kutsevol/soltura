from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="adjective_agreement",
    level="A2",
    order=30,
    title="Узгодження прикметників",
    lesson=Lesson(
        points=(
            "Прикметник узгоджується з іменником у роді й числі: un chico alto, una chica alta, unos chicos altos, unas chicas altas.",
            "Більшість прикметників на -e та на -l, -z мають одну форму для обох родів: un coche grande, una casa grande, un examen difícil, una prueba difícil. Порівняльні mejor, peor, mayor, menor теж не змінюються.",
            "Прикметники на -or, -ón, -án, -ín і назви національностей на приголосну мають жіночу форму на -a: trabajador — trabajadora, español — española. Письмовий наголос зникає: alemán — alemana, francés — francesa.",
            "Прикметник зазвичай стоїть після іменника: una casa grande. Але bueno і malo перед чоловічим іменником в однині скорочуються: un buen amigo, un mal día.",
            "Якщо іменники різного роду, прикметник стоїть у чоловічому множині: un chico y una chica simpáticos.",
        ),
        examples=(
            Example(spanish="Tengo una casa pequeña.", ukrainian="У мене маленький будинок."),
            Example(
                spanish="Mis vecinos son muy simpáticos.", ukrainian="Мої сусіди дуже приємні."
            ),
            Example(spanish="Mi amiga es española.", ukrainian="Моя подруга іспанка."),
            Example(spanish="Es un buen amigo.", ukrainian="Він хороший друг."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Mi hermana es muy ___.",
            translation="Моя сестра дуже висока.",
            options=("alto", "alta"),
            answer="alta",
            note="Hermana жіночого роду, тому alta.",
        ),
        Exercise(
            id="e2",
            sentence="Mis vecinas son muy ___.",
            translation="Мої сусідки дуже приємні.",
            options=("simpáticos", "simpáticas"),
            answer="simpáticas",
            note="Vecinas жіночого роду в множині: simpáticas.",
        ),
        Exercise(
            id="e3",
            sentence="Mi hermano y mi hermana son muy ___.",
            translation="Мій брат і моя сестра дуже високі.",
            options=("altos", "altas"),
            answer="altos",
            note="Коли іменники різного роду, прикметник стоїть у чоловічому множині.",
        ),
        Exercise(
            id="e4",
            sentence="La prueba es muy ___.",
            translation="Тест дуже складний.",
            options=("difícil", "difíciles"),
            answer="difícil",
            note="Prueba в однині, а прикметник на приголосну не змінюється за родом: difícil.",
        ),
        Exercise(
            id="e5",
            sentence="Mi vecina es ___ (alemán).",
            translation="Моя сусідка німкеня.",
            options=(),
            answer="alemana",
            note="Alemán закінчується на приголосну, тож у жіночому роді отримує -a: alemana.",
        ),
        Exercise(
            id="e6",
            sentence="Hoy es un ___ (malo) día para salir.",
            translation="Сьогодні поганий день, щоб виходити.",
            options=(),
            answer="mal",
            note="Перед чоловічим іменником в однині malo скорочується до mal.",
        ),
    ),
)
