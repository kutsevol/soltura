from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="subj_adverbial",
    level="B1",
    order=90,
    title="Subjuntivo після cuando, para que, antes de que",
    lesson=Lesson(
        points=(
            "Cuando, en cuanto, hasta que про майбутнє вимагають subjuntivo: cuando llegue, te llamo. Про звичку чи минуле кажемо indicativo: cuando llego, ceno; cuando llegué, cené.",
            "Para que — «щоб» з іншим підметом — завжди з subjuntivo: te llamo para que vengas. Коли підмет той самий, зазвичай кажемо para + інфінітив: estudio para aprender.",
            "Antes de que — «перш ніж» з іншим підметом — завжди з subjuntivo: llámame antes de que salgas. Коли підмет той самий, зазвичай кажемо antes de + інфінітив: llámame antes de salir.",
            "Для cuando, en cuanto, hasta que спитайте себе: це звичка чи вже було, чи ще лише буде? А після para que і antes de que (з іншим підметом) subjuntivo ставимо завжди.",
        ),
        examples=(
            Example(
                spanish="Cuando llegues a casa, llámame.",
                ukrainian="Коли прийдеш додому, зателефонуй мені.",
            ),
            Example(
                spanish="Cuando llego a casa, ceno.", ukrainian="Коли я приходжу додому, я вечеряю."
            ),
            Example(
                spanish="Te llamo para que sepas la verdad.",
                ukrainian="Телефоную тобі, щоб ти знав правду.",
            ),
            Example(
                spanish="Llámame antes de que salgas.",
                ukrainian="Зателефонуй мені, перш ніж вийдеш.",
            ),
            Example(
                spanish="Estudio para aprender español.",
                ukrainian="Я вчуся, щоб вивчити іспанську.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Cuando ___ a Madrid, te llamaré.",
            translation="Коли я приїду до Мадрида, зателефоную тобі.",
            options=("llegue", "llego"),
            answer="llegue",
            note="Дія ще буде, тому після cuando стоїть subjuntivo.",
        ),
        Exercise(
            id="e2",
            sentence="Siempre me ducho cuando ___ a casa.",
            translation="Я завжди приймаю душ, коли приходжу додому.",
            options=("llego", "llegue"),
            answer="llego",
            note="Звичка, а не майбутнє, тому indicativo.",
        ),
        Exercise(
            id="e3",
            sentence="Te explico esto para que lo ___ bien.",
            translation="Пояснюю тобі це, щоб ти добре зрозумів.",
            options=("entiendas", "entiendes"),
            answer="entiendas",
            note="Після para que стоїть subjuntivo: entiendas.",
        ),
        Exercise(
            id="e4",
            sentence="Hay que llamar al médico antes de que el abuelo ___.",
            translation="Треба зателефонувати лікарю, перш ніж дідові стане гірше.",
            options=("empeore", "empeora"),
            answer="empeore",
            note="Після antes de que стоїть subjuntivo: empeore.",
        ),
        Exercise(
            id="e5",
            sentence="En cuanto ___ (terminar, yo), te llamaré.",
            translation="Щойно закінчу, зателефоную тобі.",
            options=("termine", "terminaré"),
            answer="termine",
            note="Дія ще буде, тому після en cuanto стоїть subjuntivo: termine.",
        ),
        Exercise(
            id="e6",
            sentence="Estudio mucho para ___ el examen.",
            translation="Я багато вчуся, щоб скласти іспит.",
            options=("aprobar", "apruebe"),
            answer="aprobar",
            note="Підмет той самий, тому para + інфінітив.",
        ),
    ),
)
