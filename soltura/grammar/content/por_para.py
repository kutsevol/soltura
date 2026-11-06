from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="por_para",
    level="A2",
    order=120,
    title="por чи para",
    lesson=Lesson(
        points=(
            "Para — мета і напрямок: для чого, для кого, до якого терміну. Para + інфінітив означає «щоб».",
            "Por — причина, засіб, ціна й обмін, частина доби, місце, через яке проходять.",
            "Gracias por... — дякую за...: після подяки por; а gracias a означає «завдяки».",
            "Por la mañana, por la tarde, por la noche — вранці, після обіду, ввечері.",
        ),
        examples=(
            Example(
                spanish="Este regalo es para mi madre.", ukrainian="Цей подарунок для моєї мами."
            ),
            Example(spanish="Gracias por venir.", ukrainian="Дякую, що прийшли."),
            Example(
                spanish="Estudio español para vivir en España.",
                ukrainian="Вивчаю іспанську, щоб жити в Іспанії.",
            ),
            Example(spanish="Hablamos por teléfono.", ukrainian="Говоримо по телефону."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Este regalo es ___ mi madre.",
            translation="Цей подарунок для моєї мами.",
            options=("por", "para"),
            answer="para",
            note="Той, кому призначено річ, — це para.",
        ),
        Exercise(
            id="e2",
            sentence="Gracias ___ tu ayuda.",
            translation="Дякую за твою допомогу.",
            options=("por", "para"),
            answer="por",
            note="Після подяки йде por.",
        ),
        Exercise(
            id="e3",
            sentence="Estudio español ___ vivir en España.",
            translation="Вивчаю іспанську, щоб жити в Іспанії.",
            options=("por", "para"),
            answer="para",
            note="Мета («щоб») — це para.",
        ),
        Exercise(
            id="e4",
            sentence="Paseamos ___ el parque.",
            translation="Ми гуляємо парком.",
            options=("por", "para"),
            answer="por",
            note="Місце, через яке проходять чи де рухаються, — це por.",
        ),
        Exercise(
            id="e5",
            sentence="Necesito el informe ___ el viernes.",
            translation="Мені потрібен звіт до п’ятниці.",
            options=("por", "para"),
            answer="para",
            note="Термін («до п’ятниці») — це para.",
        ),
        Exercise(
            id="e6",
            sentence="Pago diez euros ___ la camiseta.",
            translation="Я плачу десять євро за футболку.",
            options=(),
            answer="por",
            note="Ціна й обмін — це por.",
        ),
    ),
)
