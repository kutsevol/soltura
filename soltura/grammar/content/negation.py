from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="negation",
    level="A2",
    order=85,
    title="Заперечення: no, nada, nadie, nunca",
    lesson=Lesson(
        points=(
            "Заперечення no стоїть перед дієсловом: no hablo francés. Відповідь «ні» теж no.",
            "Слова nada (нічого), nadie (ніхто), nunca (ніколи), tampoco (теж ні) після дієслова вимагають no перед ним: no veo a nadie, no tengo nada, no fumo nunca.",
            "Коли ці слова стоять перед дієсловом, no не потрібне: nadie viene, nunca fumo.",
            "Подвійне заперечення в іспанській правильне: no quiero nada — я нічого не хочу.",
            "Tampoco означає «теж ні»: no como carne y mi hermana tampoco.",
        ),
        examples=(
            Example(spanish="No hablo alemán.", ukrainian="Я не розмовляю німецькою."),
            Example(spanish="No veo a nadie en la calle.", ukrainian="Я нікого не бачу на вулиці."),
            Example(
                spanish="Nunca bebo café por la noche.", ukrainian="Я ніколи не п’ю каву ввечері."
            ),
            Example(spanish="No tengo nada que hacer.", ukrainian="Мені нічого робити."),
            Example(
                spanish="—No me gusta el fútbol. —A mí tampoco.",
                ukrainian="— Мені не подобається футбол. — Мені теж ні.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="No tengo ___ en la nevera.",
            translation="У мене в холодильнику нічого немає.",
            options=("nada", "algo"),
            answer="nada",
            note="Коли no стоїть перед дієсловом, «нічого» — nada.",
        ),
        Exercise(
            id="e2",
            sentence="___ come carne en mi casa.",
            translation="Ніхто в мене вдома не їсть м’ясо.",
            options=("Nadie", "No nadie"),
            answer="Nadie",
            note="Перед дієсловом no не потрібне: nadie come.",
        ),
        Exercise(
            id="e3",
            sentence="No voy ___ al cine.",
            translation="Я ніколи не ходжу в кіно.",
            options=("nunca", "algunas veces"),
            answer="nunca",
            note="Коли no стоїть перед дієсловом, «ніколи» — nunca.",
        ),
        Exercise(
            id="e4",
            sentence="No conozco a ___ en esta ciudad.",
            translation="Я нікого не знаю в цьому місті.",
            options=("nadie", "alguien"),
            answer="nadie",
            note="Коли no стоїть перед дієсловом, «нікого» — nadie, а перед людиною особове a.",
        ),
        Exercise(
            id="e5",
            sentence="—Nunca bebo café. —Yo ___.",
            translation="— Я ніколи не п’ю каву. — Я теж ні.",
            options=(),
            answer="tampoco",
            note="Теж ні — tampoco.",
        ),
        Exercise(
            id="e6",
            sentence="No quiero ___ más.",
            translation="Я більше нічого не хочу.",
            options=(),
            answer="nada",
            note="Коли no стоїть перед дієсловом, «нічого» — nada.",
        ),
    ),
)
