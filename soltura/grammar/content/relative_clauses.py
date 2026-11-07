from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="relative_clauses",
    level="B1",
    order=40,
    title="Означальні підрядні: que, donde, lo que",
    lesson=Lesson(
        points=(
            "Que — найуживаніший, про людину чи річ: el libro que leo, la chica que vive aquí. Його не можна пропускати: el libro que leo, а не «el libro leo».",
            "Donde — про місце: la ciudad donde vivo es pequeña.",
            "Після прийменника зазвичай стоїть el que, la que, los que, las que (про людей також quien): la chica con la que hablo, el amigo con quien viajo. Після a, con, de, en, por артикль іноді опускають (la casa en que vivo), але форма з артиклем частіша й безпечніша.",
            "Lo que означає «те, що»: lo que dices es verdad, no entiendo lo que dices.",
            "Пояснювальна підрядна відокремлюється комами: mi hermano, que vive en Madrid, viene mañana.",
        ),
        examples=(
            Example(
                spanish="El libro que estoy leyendo es muy largo.",
                ukrainian="Книжка, яку я читаю, дуже довга.",
            ),
            Example(
                spanish="La ciudad donde vivo es pequeña.", ukrainian="Місто, де я живу, маленьке."
            ),
            Example(
                spanish="La chica con la que hablaba es mi vecina.",
                ukrainian="Дівчина, з якою я розмовляв, моя сусідка.",
            ),
            Example(spanish="No entiendo lo que dices.", ukrainian="Я не розумію, що ти кажеш."),
            Example(
                spanish="Mi hermano, que vive en Madrid, viene mañana.",
                ukrainian="Мій брат, який живе в Мадриді, приїде завтра.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="El piso ___ alquilé es muy luminoso.",
            translation="Квартира, яку я орендував, дуже світла.",
            options=("que", "donde"),
            answer="que",
            note="Que тут — додаток дієслова alquilé («орендував що?»), а не місце, тому donde не підходить.",
        ),
        Exercise(
            id="e2",
            sentence="El pueblo ___ nací está en la montaña.",
            translation="Село, де я народився, у горах.",
            options=("donde", "que"),
            answer="donde",
            note="Підрядна описує місце, тому donde.",
        ),
        Exercise(
            id="e3",
            sentence="La mujer ___ trabajo es muy amable.",
            translation="Жінка, з якою я працюю, дуже привітна.",
            options=("con la que", "con lo que"),
            answer="con la que",
            note="Після прийменника перед людиною зазвичай la que або quien: con la que. Con lo que — про цілу ситуацію.",
        ),
        Exercise(
            id="e4",
            sentence="No sé ___ quieres.",
            translation="Я не знаю, чого ти хочеш.",
            options=("lo que", "que"),
            answer="lo que",
            note="«Те, що» без іменника — lo que.",
        ),
        Exercise(
            id="e5",
            sentence="La película de ___ te hablé es muy buena.",
            translation="Фільм, про який я тобі розповідав, дуже хороший.",
            options=("la que", "lo que"),
            answer="la que",
            note="Película — конкретна річ, тож після de стоїть la que; lo que — про цілу думку.",
        ),
        Exercise(
            id="e6",
            sentence="El restaurante ___ comimos ayer era caro.",
            translation="Ресторан, де ми вчора їли, був дорогий.",
            options=("donde", "que"),
            answer="donde",
            note="Підрядна описує місце, тому donde.",
        ),
    ),
)
