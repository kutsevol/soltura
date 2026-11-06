from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="ser_estar",
    level="A2",
    order=40,
    title="ser чи estar",
    lesson=Lesson(
        points=(
            "Ser каже, що це або хто це і який він: професія, національність, походження, характеристика (es alto, es simpático), матеріал, час і дата.",
            "Estar каже, де це і який стан зараз: місцезнаходження, настрій, самопочуття.",
            "Час події — ser: la reunión es a las cinco. Місце, де відбувається свято чи зустріч, зазвичай теж ser (la fiesta es en mi casa), а де щось знаходиться — estar.",
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
            sentence="Mi madre ___ de Ucrania.",
            translation="Моя мама з України.",
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
            sentence="La clase ___ a las nueve.",
            translation="Урок о дев’ятій.",
            options=("es", "está"),
            answer="es",
            note="Час події — це ser.",
        ),
        Exercise(
            id="e5",
            sentence="Mi hermano ___ ingeniero.",
            translation="Мій брат інженер.",
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
