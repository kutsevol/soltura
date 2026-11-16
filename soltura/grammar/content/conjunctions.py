from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="conjunctions",
    level="A1",
    order=92,
    title="Сполучники: y, o, pero, ni",
    lesson=Lesson(
        points=(
            "Y — «і, та»: з’єднує однакове. Soy ucraniana y vivo en Madrid.",
            "O — «або, чи»: вибір. ¿Bebes té o café?",
            "Pero — «але»: протиставлення. Hablo español, pero no hablo francés.",
            "Ni — «ні... ні» у запереченні: No como ni carne ni pescado. Можна й коротше, з одним ni: No como carne ni pescado («не їм м’яса ні риби»).",
            "Uno... otro — «один... інший» без іменника, про жінок una... otra: Uno habla español, otro habla francés.",
        ),
        examples=(
            Example(
                spanish="Soy ucraniana y vivo en Madrid.", ukrainian="Я українка й живу в Мадриді."
            ),
            Example(spanish="¿Bebes té o café?", ukrainian="Ти п’єш чай чи каву?"),
            Example(
                spanish="Hablo español, pero no hablo francés.",
                ukrainian="Я розмовляю іспанською, але не розмовляю французькою.",
            ),
            Example(spanish="No como ni carne ni pescado.", ukrainian="Я не їм ні м’яса, ні риби."),
            Example(
                spanish="Uno habla español, otro habla francés.",
                ukrainian="Один розмовляє іспанською, інший — французькою.",
            ),
            Example(
                spanish="Mi hermana es alta y morena.", ukrainian="Моя сестра висока й темноволоса."
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Tengo hambre, ___ no tengo dinero.",
            translation="Я голодний, але в мене немає грошей.",
            options=("pero", "o"),
            answer="pero",
            note="Протиставлення («але»): pero.",
        ),
        Exercise(
            id="e2",
            sentence="¿Vives en Madrid ___ en Valencia?",
            translation="Ти живеш у Мадриді чи у Валенсії?",
            options=("o", "y"),
            answer="o",
            note="Вибір між двома: o.",
        ),
        Exercise(
            id="e3",
            sentence="Mi hermano estudia ___ trabaja.",
            translation="Мій брат вчиться й працює.",
            options=("y", "ni"),
            answer="y",
            note="З’єднуємо дві дії: y.",
        ),
        Exercise(
            id="e4",
            sentence="No tengo ni hermanos ___ hermanas.",
            translation="У мене немає ні братів, ні сестер.",
            options=("ni", "pero"),
            answer="ni",
            note="У запереченні «ні... ні»: no tengo... ni.",
        ),
        Exercise(
            id="e5",
            sentence="No bebo ni café ___ té.",
            translation="Я не п’ю ні кави, ні чаю.",
            options=(),
            answer="ni",
            note="У запереченні «ні... ні»: ni.",
        ),
        Exercise(
            id="e6",
            sentence="Soy español, ___ vivo en Londres.",
            translation="Я іспанець, але живу в Лондоні.",
            options=(),
            answer="pero",
            note="Протиставлення («але»): pero.",
        ),
    ),
)
