from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="direct_object_pronouns",
    level="A2",
    order=90,
    title="Прямі займенники: lo, la, los, las",
    lesson=Lesson(
        points=(
            "Прямий додаток — те, що ми бачимо, купуємо, читаємо: compro el pan — lo compro.",
            "Займенники: me, te, lo, la, nos, os, los, las. Lo, la, los, las узгоджуються з тим, що замінюють, у роді й числі.",
            "Займенник стоїть перед відмінюваним дієсловом: la veo, no lo sé. З інфінітивом він пишеться разом з ним (voy a verla, quiero comprarlo) або стоїть перед першим дієсловом (la voy a ver, lo quiero comprar).",
            "Lo може замінювати цілу думку: ¿sabes que Ana viene? — sí, lo sé.",
            "В Іспанії про чоловіка часто кажуть le (le veo), і це припустимо; про речі та про жінок тільки lo, la, los, las. Тут вчимо lo.",
        ),
        examples=(
            Example(spanish="¿El pan? Lo compro cada día.", ukrainian="Хліб? Я купую його щодня."),
            Example(spanish="La veo todos los días.", ukrainian="Я бачу її щодня."),
            Example(spanish="Los tengo en casa.", ukrainian="Вони в мене вдома."),
            Example(spanish="Voy a comprarlo mañana.", ukrainian="Куплю це завтра."),
            Example(spanish="No lo sé.", ukrainian="Я цього не знаю."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="¿La puerta? ___ cierro yo.",
            translation="Двері? Зачиню я.",
            options=("lo", "la"),
            answer="la",
            note="Puerta жіночого роду: la.",
        ),
        Exercise(
            id="e2",
            sentence="¿Los billetes? ___ tengo aquí.",
            translation="Квитки? Вони в мене тут.",
            options=("lo", "los"),
            answer="los",
            note="Billetes чоловічого роду в множині: los.",
        ),
        Exercise(
            id="e3",
            sentence="¿El libro? ___ leo esta noche.",
            translation="Книжка? Прочитаю сьогодні ввечері.",
            options=("lo", "le"),
            answer="lo",
            note="Libro чоловічого роду, і це прямий додаток: lo.",
        ),
        Exercise(
            id="e4",
            sentence="Ana viene mañana. Ya ___ sé.",
            translation="Ана приїде завтра. Я це вже знаю.",
            options=("lo", "la"),
            answer="lo",
            note="Lo замінює цілу думку («Ана приїде»).",
        ),
        Exercise(
            id="e5",
            sentence="¿Las ventanas? ___ abro por la mañana.",
            translation="Вікна? Відчиняю вранці.",
            options=(),
            answer="las",
            note="Ventanas жіночого роду в множині: las.",
        ),
        Exercise(
            id="e6",
            sentence="¿Dónde está María? No ___ veo.",
            translation="Де Марія? Я її не бачу.",
            options=(),
            answer="la",
            note="Марія — вона, тому la.",
        ),
    ),
)
