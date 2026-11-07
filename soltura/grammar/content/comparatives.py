from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="comparatives",
    level="A2",
    order=75,
    title="Порівняння: más que, menos que, tan como",
    lesson=Lesson(
        points=(
            "Більше: más + прикметник + que: Madrid es más grande que Valencia. Менше: menos + прикметник + que.",
            "Однаково: tan + прикметник + como: mi casa es tan grande como la tuya. З іменником: tanto, tanta, tantos, tantas + іменник + como: tengo tantos libros como tú.",
            "Неправильні: bueno — mejor, malo — peor. Про якість, фільм, річ кажемо mejor, а не más bueno (más bueno вживають про доброту людини чи смак їжі: es más bueno que el pan). Для розміру: más grande, más pequeño; для віку: mayor, menor (mi hermano mayor), без más.",
            "У ствердженнях з числами після más і menos стоїть de, а не que: hay más de cien personas.",
            "Найвищий ступінь: el, la, los, las + más + прикметник: es el más alto de la clase.",
        ),
        examples=(
            Example(
                spanish="Madrid es más grande que Valencia.",
                ukrainian="Мадрид більший за Валенсію.",
            ),
            Example(
                spanish="Este piso es menos caro que el otro.",
                ukrainian="Ця квартира дешевша за ту.",
            ),
            Example(
                spanish="Mi casa es tan grande como la tuya.",
                ukrainian="Мій дім такий самий великий, як твій.",
            ),
            Example(
                spanish="Esta pizza es mejor que la de ayer.",
                ukrainian="Ця піца краща за вчорашню.",
            ),
            Example(spanish="Es el más alto de la clase.", ukrainian="Він найвищий у класі."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Mi hermano es ___ alto que yo.",
            translation="Мій брат вищий за мене.",
            options=("más", "tan"),
            answer="más",
            note="Для «більше» кажемо más ... que.",
        ),
        Exercise(
            id="e2",
            sentence="Mi café es ___ caliente como el tuyo.",
            translation="Моя кава така сама гаряча, як твоя.",
            options=("tan", "más"),
            answer="tan",
            note="Для «однаково» кажемо tan ... como.",
        ),
        Exercise(
            id="e3",
            sentence="Esta película es ___ que la otra.",
            translation="Цей фільм кращий за той.",
            options=("mejor", "más mejor"),
            answer="mejor",
            note="Mejor вже означає «кращий»: más mejor не кажемо.",
        ),
        Exercise(
            id="e4",
            sentence="Mi hermana tiene ___ amigas como yo.",
            translation="У моєї сестри стільки ж подруг, як у мене.",
            options=("tantas", "tantos"),
            answer="tantas",
            note="Amigas жіночого роду в множині, тому tantas.",
        ),
        Exercise(
            id="e5",
            sentence="Somos menos ___ veinte en la clase.",
            translation="Нас у класі менше ніж двадцять.",
            options=("de", "que"),
            answer="de",
            note="З числами після menos стоїть de.",
        ),
        Exercise(
            id="e6",
            sentence="El Everest es el ___ alto del mundo.",
            translation="Еверест — найвища гора світу.",
            options=(),
            answer="más",
            note="Найвищий ступінь: el más alto.",
        ),
    ),
)
