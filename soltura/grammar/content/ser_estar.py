from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="ser_estar",
    level="A2",
    order=40,
    title="ser чи estar",
    lesson=Lesson(
        points=(
            "Ser каже, що це або хто це: професія, національність, походження, матеріал, час і дата.",
            "Estar каже, де це і який стан зараз: місцезнаходження, настрій, самопочуття.",
            "Місце події (свята, зустрічі) — ser: La fiesta es en mi casa.",
            "Деякі прикметники міняють значення: es aburrido (він нудний) — está aburrido (йому нудно); es listo (він розумний) — está listo (він готовий).",
        ),
        examples=(
            Example(
                spanish="Soy ucraniano y vivo en Valencia.",
                ukrainian="Я українець і живу у Валенсії.",
            ),
            Example(spanish="Mi hermano es médico.", ukrainian="Мій брат лікар."),
            Example(spanish="El café está frío.", ukrainian="Кава холодна."),
            Example(spanish="La reunión es a las cinco.", ukrainian="Зустріч о п’ятій."),
            Example(spanish="Hoy estoy muy cansada.", ukrainian="Сьогодні я дуже втомлена."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Mi madre ___ de Kyiv.",
            translation="Моя мама з Києва.",
            options=("es", "está"),
            answer="es",
            note="Походження — це ser.",
        ),
        Exercise(
            id="e2",
            sentence="El supermercado ___ cerca de aquí.",
            translation="Супермаркет близько звідси.",
            options=("es", "está"),
            answer="está",
            note="Де щось знаходиться — це estar.",
        ),
        Exercise(
            id="e3",
            sentence="Hoy ___ muy cansado.",
            translation="Сьогодні я дуже втомлений.",
            options=("soy", "estoy"),
            answer="estoy",
            note="Стан зараз — це estar.",
        ),
        Exercise(
            id="e4",
            sentence="La fiesta ___ en mi casa.",
            translation="Свято в мене вдома.",
            options=("es", "está"),
            answer="es",
            note="Місце, де відбувається подія, — це ser.",
        ),
        Exercise(
            id="e5",
            sentence="Mi hermano ___ médico.",
            translation="Мій брат лікар.",
            options=(),
            answer="es",
            note="Професія — це ser.",
        ),
        Exercise(
            id="e6",
            sentence="Las llaves ___ en la mesa.",
            translation="Ключі лежать на столі.",
            options=(),
            answer="están",
            note="Де щось знаходиться — це estar; llaves у множині, тому están.",
        ),
    ),
)
