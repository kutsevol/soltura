from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="tener_que_hay_que",
    level="A2",
    order=44,
    title="tener que, hay que, deber: треба й слід",
    lesson=Lesson(
        points=(
            "Tener que + інфінітив означає «мушу, мусиш»: tengo que trabajar. Змінюється лише tener, а que + інфінітив ні.",
            "Hay que + інфінітив — «треба» для всіх, безособово: hay que pagar el alquiler. Hay не змінюється за особами.",
            "Deber + інфінітив — «слід, повинен»: debes descansar. Часто звучить як порада чи моральний обов’язок, а tener que — як конкретна потреба.",
            "Не плутайте tener і tener que: tengo hambre — я голодний; tengo que comer — мені треба поїсти.",
        ),
        examples=(
            Example(
                spanish="Tengo que trabajar el sábado.", ukrainian="Мені треба працювати в суботу."
            ),
            Example(
                spanish="Hay que pagar antes del día cinco.",
                ukrainian="Треба заплатити до п’ятого числа.",
            ),
            Example(spanish="Debes descansar más.", ukrainian="Тобі слід більше відпочивати."),
            Example(spanish="¿Tienes que irte ya?", ukrainian="Тобі вже треба йти?"),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Yo ___ que madrugar mañana.",
            translation="Завтра мені треба рано вставати.",
            options=("tengo", "hay"),
            answer="tengo",
            note="Підмет yo, тому tengo que; hay que не має підмета.",
        ),
        Exercise(
            id="e2",
            sentence="Aquí ___ que pagar antes de entrar.",
            translation="Тут усім треба платити перед входом.",
            options=("hay", "hace"),
            answer="hay",
            note="Коли «треба» для всіх, кажемо hay que.",
        ),
        Exercise(
            id="e3",
            sentence="Mis padres ___ que viajar mañana.",
            translation="Моїм батькам треба завтра їхати.",
            options=("tienen", "tengo"),
            answer="tienen",
            note="Mis padres — вони, тому tienen que.",
        ),
        Exercise(
            id="e4",
            sentence="Los niños ___ dormir más.",
            translation="Дітям слід більше спати.",
            options=("deben", "debes"),
            answer="deben",
            note="Los niños — вони, тому deben.",
        ),
        Exercise(
            id="e5",
            sentence="Mi hermana ___ que estudiar para el examen.",
            translation="Моїй сестрі треба вчитися до іспиту.",
            options=("tiene", "tienen"),
            answer="tiene",
            note="Підмет mi hermana, тому tiene que.",
        ),
        Exercise(
            id="e6",
            sentence="Tenemos ___ limpiar la casa hoy.",
            translation="Нам треба сьогодні прибрати вдома.",
            options=(),
            answer="que",
            note="Tener que + інфінітив: tenemos que limpiar.",
        ),
    ),
)
