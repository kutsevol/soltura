from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="reflexive_verbs",
    level="A1",
    order=95,
    title="Зворотні дієслова: levantarse",
    lesson=Lesson(
        points=(
            "Зворотне дієслово в інфінітиві закінчується на -se: levantarse (вставати), ducharse (приймати душ), llamarse (називатися). Дія повертається до того, хто її робить.",
            "Займенники: me, te, se, nos, os, se. В особових формах вони стоять перед дієсловом: me levanto, te levantas, se levanta, nos levantamos, os levantáis, se levantan.",
            "З інфінітивом займенник відповідає підмету: quiero ducharme, quieres ducharte, quiere ducharse.",
            "Багато щоденних дій в іспанській зворотні: despertarse (прокидатися), acostarse (лягати спати), vestirse (одягатися).",
            "З частинами тіла й одягом зазвичай ставимо означений артикль, а не присвійне mi: me lavo las manos, me pongo el abrigo.",
        ),
        examples=(
            Example(spanish="Me llamo Artur.", ukrainian="Мене звати Артур."),
            Example(
                spanish="Mis hijos se levantan a las siete.", ukrainian="Мої діти встають о сьомій."
            ),
            Example(
                spanish="Nos acostamos tarde los sábados.",
                ukrainian="Ми лягаємо спати пізно по суботах.",
            ),
            Example(
                spanish="Me lavo las manos antes de comer.", ukrainian="Я мию руки перед їжею."
            ),
            Example(spanish="Voy a ducharme.", ukrainian="Піду прийму душ."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Yo ___ levanto a las siete.",
            translation="Я встаю о сьомій.",
            options=("me", "se"),
            answer="me",
            note="Підмет yo, тому займенник me.",
        ),
        Exercise(
            id="e2",
            sentence="Mi hermana ___ llama Laura.",
            translation="Мою сестру звати Лаура.",
            options=("se", "te"),
            answer="se",
            note="Підмет mi hermana — вона, тому se.",
        ),
        Exercise(
            id="e3",
            sentence="Nosotros ___ acostamos a las once.",
            translation="Ми лягаємо спати об одинадцятій.",
            options=("nos", "os"),
            answer="nos",
            note="Підмет nosotros, тому nos.",
        ),
        Exercise(
            id="e4",
            sentence="Los niños quieren ___ pronto.",
            translation="Діти хочуть скоро лягти спати.",
            options=("acostarse", "acostarte"),
            answer="acostarse",
            note="Підмет los niños — вони, тому в інфінітиві -se.",
        ),
        Exercise(
            id="e5",
            sentence="Tú ___ (levantarse) muy temprano.",
            translation="Ти дуже рано встаєш.",
            options=(),
            answer="te levantas",
            note="Підмет tú: займенник te і форма levantas.",
        ),
        Exercise(
            id="e6",
            sentence="Ellos ___ (llamarse) Pedro y Ana.",
            translation="Їх звати Педро та Ана.",
            options=(),
            answer="se llaman",
            note="Підмет ellos: займенник se і форма llaman.",
        ),
    ),
)
