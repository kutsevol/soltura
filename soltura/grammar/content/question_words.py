from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="question_words",
    level="A1",
    order=45,
    title="Питальні слова: qué, quién, cuánto, dónde, cómo, por qué",
    lesson=Lesson(
        points=(
            "Питальне слово стоїть на початку питання (після прийменника, якщо він є, як у por qué) і завжди пишеться з наголосом: ¿Qué?, ¿Quién?, ¿Dónde?, ¿Cómo?. Іспанське питання починається знаком ¿ і закінчується знаком ?.",
            "Qué — «що»: ¿Qué lees? ¿Qué comes? Перед іменником — «який»: ¿Qué libro lees? Qué не змінюється.",
            "Quién — «хто» про одну людину, quiénes — про кількох: ¿Quién es María? ¿Quiénes son Pedro y Ana?",
            "Cuánto — «скільки». Перед іменником змінюється за родом і числом: ¿Cuántos años tienes? ¿Cuántas hermanas tienes?",
            "Dónde — «де», adónde — «куди» (пишуть і a dónde), cómo — «як». Вони не змінюються: ¿Dónde vives? ¿Adónde vas? ¿Cómo estás?",
            "¿Por qué? двома словами й з наголосом — «чому»; porque одним словом і без наголосу — «бо, тому що»: ¿Por qué estudias español? — Porque vivo en España.",
        ),
        examples=(
            Example(spanish="¿Qué estudias?", ukrainian="Що ти вивчаєш?"),
            Example(spanish="¿Quién es María?", ukrainian="Хто така Марія?"),
            Example(spanish="¿Cuántos años tienes?", ukrainian="Скільки тобі років?"),
            Example(spanish="¿Dónde vives?", ukrainian="Де ти живеш?"),
            Example(spanish="¿Cómo te llamas?", ukrainian="Як тебе звати?"),
            Example(
                spanish="¿Por qué estudias español? Porque vivo en España.",
                ukrainian="Чому ти вивчаєш іспанську? Бо я живу в Іспанії.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="¿___ trabajas?",
            translation="Де ти працюєш?",
            options=("Dónde", "Quién"),
            answer="Dónde",
            note="Питаємо про місце: dónde.",
        ),
        Exercise(
            id="e2",
            sentence="¿___ es Pedro? Es un amigo.",
            translation="Хто такий Педро? Це друг.",
            options=("Quién", "Dónde"),
            answer="Quién",
            note="Питаємо про людину: quién. Dónde питає про місце.",
        ),
        Exercise(
            id="e3",
            sentence="¿___ hermanos tienes?",
            translation="Скільки в тебе братів і сестер?",
            options=("Cuántos", "Cuántas"),
            answer="Cuántos",
            note="Hermanos — чоловічий рід, множина: cuántos.",
        ),
        Exercise(
            id="e4",
            sentence="—¿___ vives aquí? —Porque trabajo aquí.",
            translation="— Чому ти живеш тут? — Бо я тут працюю.",
            options=("Por qué", "Porque"),
            answer="Por qué",
            note="У питанні «чому» — двома словами й з наголосом: por qué. Porque — «бо», у відповіді.",
        ),
        Exercise(
            id="e5",
            sentence="¿___ lees? Leo un libro.",
            translation="Що ти читаєш? Я читаю книгу.",
            options=(),
            answer="Qué",
            note="Питаємо про предмет: qué, з наголосом.",
        ),
        Exercise(
            id="e6",
            sentence="Chicos, ¿___ estáis hoy?",
            translation="Діти, як ви сьогодні?",
            options=(),
            answer="Cómo",
            note="Питаємо «як»: cómo, з наголосом.",
        ),
    ),
)
