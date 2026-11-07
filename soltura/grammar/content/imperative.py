from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="imperative",
    level="A2",
    order=140,
    title="Наказовий спосіб: habla, come, escribe",
    lesson=Lesson(
        points=(
            "Ствердний наказ для tú має ту саму форму, що й él у теперішньому часі: hablar — habla, comer — come, escribir — escribe.",
            "Для usted форма «навпаки»: -ar дає -e, а -er і -ir дають -a: hable, coma, escriba. Для vosotros в Іспанії беремо інфінітив і замінюємо -r на -d: hablad, comed, escribid.",
            "Вісім неправильних форм для tú треба знати: di (decir), haz (hacer), ve (ir), pon (poner), sal (salir), sé (ser), ten (tener), ven (venir).",
            "Займенники пишуться разом із ствердним наказом, і часто з’являється знак наголосу: cómpralo, dime, siéntate.",
        ),
        examples=(
            Example(
                spanish="Habla más despacio, por favor.", ukrainian="Говори повільніше, будь ласка."
            ),
            Example(spanish="Come algo antes de salir.", ukrainian="З’їж щось перед виходом."),
            Example(spanish="Ven aquí un momento.", ukrainian="Іди сюди на хвилинку."),
            Example(spanish="Pase, por favor.", ukrainian="Проходьте, будь ласка."),
            Example(spanish="Dime la verdad.", ukrainian="Скажи мені правду."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="¿Quieres este libro? ___.",
            translation="Хочеш цю книжку? Купи її.",
            options=("Cómpralo", "Lo compra"),
            answer="Cómpralo",
            note="У ствердному наказі займенник пишеться разом із дієсловом: cómpralo.",
        ),
        Exercise(
            id="e2",
            sentence="___ los deberes antes de cenar.",
            translation="Зроби домашнє завдання перед вечерею.",
            options=("Haz", "Hace"),
            answer="Haz",
            note="Hacer має неправильний наказ для tú: haz.",
        ),
        Exercise(
            id="e3",
            sentence="Señor García, ___ (pasar, usted) por aquí, por favor.",
            translation="Пане Гарсіа, проходьте сюди, будь ласка.",
            options=(),
            answer="pase",
            note="Для usted -ar дає -e: pase.",
        ),
        Exercise(
            id="e4",
            sentence="Niños, ___ vuestro nombre aquí.",
            translation="Діти, напишіть тут своє ім’я.",
            options=("escribid", "escribe"),
            answer="escribid",
            note="Для vosotros в інфінітиві -r змінюємо на -d: escribid.",
        ),
        Exercise(
            id="e5",
            sentence="Pablo, ___ (decir, tú) la verdad.",
            translation="Пабло, скажи правду.",
            options=(),
            answer="di",
            note="Decir має неправильний наказ для tú: di.",
        ),
        Exercise(
            id="e6",
            sentence="Cuando llegues a casa, ___ (poner) la mesa.",
            translation="Коли прийдеш додому, накрий на стіл.",
            options=(),
            answer="pon",
            note="Poner має неправильний наказ для tú: pon.",
        ),
    ),
)
