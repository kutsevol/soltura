from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="indirect_object_pronouns",
    level="A2",
    order=100,
    title="Непрямі займенники: le, les, se lo",
    lesson=Lesson(
        points=(
            "Непрямий додаток — кому щось даємо, пишемо, кажемо: doy el libro a Ana — le doy el libro.",
            "Me, te, le, nos, os, les. Le і les однакові для чоловіків і жінок.",
            "Коли додаток із a стоїть перед дієсловом, займенник обов’язковий: a Ana le doy un regalo.",
            "Коли поруч два займенники, непрямий стоїть перед прямим: te lo explico, me la da.",
            "Le або les перед lo, la, los, las стає se: le doy el libro — se lo doy. Ніколи не кажемо le lo.",
        ),
        examples=(
            Example(
                spanish="Le escribo un mensaje a mi madre.", ukrainian="Я пишу повідомлення мамі."
            ),
            Example(spanish="Les doy las llaves a mis vecinos.", ukrainian="Я даю ключі сусідам."),
            Example(
                spanish="Me dan una cita para el lunes.", ukrainian="Мені дають запис на понеділок."
            ),
            Example(
                spanish="¿El libro? Se lo doy mañana.",
                ukrainian="Книжка? Дам її завтра (йому чи їй).",
            ),
            Example(spanish="Te lo explico luego.", ukrainian="Поясню тобі це потім."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="A mis padres ___ escribo cada semana.",
            translation="Батькам я пишу щотижня.",
            options=("le", "les"),
            answer="les",
            note="Mis padres — вони, тому les.",
        ),
        Exercise(
            id="e2",
            sentence="A Ana ___ doy un regalo.",
            translation="Ані я даю подарунок.",
            options=("le", "lo"),
            answer="le",
            note="Ана — кому даємо, тому le.",
        ),
        Exercise(
            id="e3",
            sentence="¿El libro? A Pedro ___ doy mañana.",
            translation="Книжку? Педрові я віддам її завтра.",
            options=("le lo", "se lo"),
            answer="se lo",
            note="Le перед lo стає se: se lo.",
        ),
        Exercise(
            id="e4",
            sentence="Mi padre ___ prepara la cena.",
            translation="Мій тато готує мені вечерю.",
            options=("me", "mí"),
            answer="me",
            note="Кому готує — мені, займенник me.",
        ),
        Exercise(
            id="e5",
            sentence="A los niños ___ cuento un cuento.",
            translation="Дітям я розповідаю казку.",
            options=(),
            answer="les",
            note="Los niños — вони, тому les.",
        ),
        Exercise(
            id="e6",
            sentence="¿Las llaves? A mi vecina ___ las doy mañana.",
            translation="Ключі? Сусідці я віддам їх завтра.",
            options=(),
            answer="se",
            note="Le перед las стає se: se las.",
        ),
    ),
)
