from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="imperative_negative",
    level="B1",
    order=15,
    title="Заперечний наказ: no hables, no comas",
    lesson=Lesson(
        points=(
            "Заперечний наказ для tú бере форми підрядного способу, а не ствердного наказу: habla — no hables, come — no comas, escribe — no escribas.",
            "Для tú -ar дає -es, а -er і -ir дають -as: no hables, no comas. Для usted -e і -a: no hable, no coma. Для vosotros: no habléis, no comáis. Правопис змінюється: llegar — no llegues, buscar — no busques, empezar — no empieces.",
            "Основу беремо з форми yo теперішнього часу: hago — no hagas, digo — no digas, salgo — no salgas, vengo — no vengas, tengo — no tengas. Є винятки: no vayas (ir), no seas (ser), no sepas (saber), no des (dar), no estés (estar).",
            "У заперечному наказі займенник стоїть перед дієсловом: no lo hagas, no te levantes. У ствердному він стоїть після: hazlo, levántate.",
        ),
        examples=(
            Example(spanish="No hables tan rápido.", ukrainian="Не говори так швидко."),
            Example(spanish="No comas eso.", ukrainian="Не їж цього."),
            Example(spanish="No vengas tarde.", ukrainian="Не приходь пізно."),
            Example(spanish="No lo hagas, por favor.", ukrainian="Не роби цього, будь ласка."),
            Example(spanish="No vayas solo.", ukrainian="Не ходи сам."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="No ___ levantes todavía.",
            translation="Не вставай ще.",
            options=("te", "me"),
            answer="te",
            note="У заперечному наказі займенник стоїть перед дієсловом, для tú це te.",
        ),
        Exercise(
            id="e2",
            sentence="No ___ más pastel.",
            translation="Не їж більше торта.",
            options=("comas", "come"),
            answer="comas",
            note="Заперечний наказ для tú від comer: no comas.",
        ),
        Exercise(
            id="e3",
            sentence="No ___ eso, por favor.",
            translation="Не роби цього, будь ласка.",
            options=("hagas", "haz"),
            answer="hagas",
            note="Основа з форми yo hago: no hagas.",
        ),
        Exercise(
            id="e4",
            sentence="No ___ de casa sin abrigo.",
            translation="Не виходь з дому без пальта.",
            options=("salgas", "sales"),
            answer="salgas",
            note="Основа з форми yo salgo: no salgas.",
        ),
        Exercise(
            id="e5",
            sentence="No ___ (tener, tú) miedo.",
            translation="Не бійся.",
            options=(),
            answer="tengas",
            note="Основа з форми yo tengo: no tengas.",
        ),
        Exercise(
            id="e6",
            sentence="No ___ tan tarde, chicos.",
            translation="Не приходьте так пізно, діти.",
            options=("lleguéis", "llegáis"),
            answer="lleguéis",
            note="Для vosotros від llegar: no lleguéis, з gu перед e.",
        ),
    ),
)
