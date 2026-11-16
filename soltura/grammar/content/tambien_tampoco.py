from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="tambien_tampoco",
    level="A1",
    order=90,
    title="también і tampoco: теж і теж ні",
    lesson=Lesson(
        points=(
            "También — «теж, також»: додаємо до того, що сказали. Soy alemán. — Yo también. («Я німець. — Я теж.»)",
            "Tampoco — «теж ні, також не»: додаємо до заперечення. No hablo francés. — Yo tampoco. («Я не розмовляю французькою. — Я теж ні.»)",
            "Правило просте: після «так» — también, після «ні» — tampoco. Не кажемо yo también no і yo no también: у запереченні tampoco. Коли не погоджуємося, кажемо Yo no або Yo sí: Soy alemán. — Yo no. No hablo francés. — Yo sí.",
            "Tampoco, як і no, робить речення заперечним. Перед дієсловом no не потрібне: Yo tampoco voy. Після дієслова no треба: No voy tampoco.",
            "Часто відповідаємо без дієслова: Yo también, Yo tampoco, а про когось іншого: Mi hermana también, Mis padres tampoco.",
        ),
        examples=(
            Example(
                spanish="Hablo español. Mi madre también habla español.",
                ukrainian="Я розмовляю іспанською. Моя мама теж розмовляє іспанською.",
            ),
            Example(spanish="Soy alemán. —Yo también.", ukrainian="Я німець. — Я теж."),
            Example(
                spanish="No hablo francés. —Yo tampoco.",
                ukrainian="Я не розмовляю французькою. — Я теж ні.",
            ),
            Example(spanish="Yo tampoco voy.", ukrainian="Я теж не йду."),
            Example(
                spanish="Ana vive en Madrid y su hermano también.",
                ukrainian="Ана живе в Мадриді, і її брат теж.",
            ),
            Example(
                spanish="No como carne y mi hermana tampoco.",
                ukrainian="Я не їм м’яса, і моя сестра теж ні.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Vivo en Valencia. —Yo ___.",
            translation="Я живу у Валенсії. — Я теж.",
            options=("también", "tampoco"),
            answer="también",
            note="Після твердження («я живу») — también.",
        ),
        Exercise(
            id="e2",
            sentence="No bebo café. —Yo ___.",
            translation="Я не п’ю каву. — Я теж ні.",
            options=("también", "tampoco"),
            answer="tampoco",
            note="Після заперечення («я не п’ю») — tampoco.",
        ),
        Exercise(
            id="e3",
            sentence="Mi padre vive en Valencia y mi madre ___.",
            translation="Мій тато живе у Валенсії, і мама теж.",
            options=("también", "tampoco"),
            answer="también",
            note="Обидва живуть у Валенсії: також, también.",
        ),
        Exercise(
            id="e4",
            sentence="No vivo en Madrid y mi hermana ___.",
            translation="Я не живу в Мадриді, і сестра теж (не живе).",
            options=("también", "tampoco"),
            answer="tampoco",
            note="Обоє не живуть у Мадриді: tampoco.",
        ),
        Exercise(
            id="e5",
            sentence="Estudio inglés y mis amigos ___.",
            translation="Я вивчаю англійську, і мої друзі теж.",
            options=(),
            answer="también",
            note="Твердження плюс твердження: también.",
        ),
        Exercise(
            id="e6",
            sentence="Ellos no hablan inglés. Nosotros ___.",
            translation="Вони не говорять англійською. Ми теж (не говоримо).",
            options=(),
            answer="tampoco",
            note="Заперечення плюс заперечення: tampoco.",
        ),
    ),
)
