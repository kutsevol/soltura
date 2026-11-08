from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="subj_wishes",
    level="B1",
    order=70,
    title="Subjuntivo: хочу, щоб...",
    lesson=Lesson(
        points=(
            "Після дієслів бажання (querer, esperar, preferir, necesitar) з іншим підметом стоїть que і subjuntivo: quiero que vengas, espero que te guste. З дієсловами прохання й дозволу (pedir, permitir, prohibir, mandar) можливі обидві конструкції: te prohíbo que fumes і te prohíbo fumar.",
            "Коли підмет той самий, кажемо інфінітив: quiero venir — я хочу прийти, але quiero que vengas — я хочу, щоб ти прийшов.",
            "Теперішній subjuntivo: -ar дає -e, -es, -e, -emos, -éis, -en; -er і -ir дають -a, -as, -a, -amos, -áis, -an: hable, coma, viva. Основу беремо з форми yo: tengo — tenga, hago — haga, salgo — salga, vengo — venga.",
            "У дієсловах із чергуванням голосних форми nosotros і vosotros повертають голосну інфінітива: pensar — pensemos, poder — podamos; у дієсловах на -ir вона змінюється: dormir — durmamos, sentir — sintamos.",
            "Неправильні: ser — sea, ir — vaya, saber — sepa, estar — esté, dar — dé, haber — haya.",
            "Ті самі форми в заперечному наказі (no hables) і в наказі для usted (hable).",
        ),
        examples=(
            Example(
                spanish="Quiero que vengas a mi fiesta.",
                ukrainian="Я хочу, щоб ти прийшов на мою вечірку.",
            ),
            Example(
                spanish="Mi madre quiere que yo estudie más.",
                ukrainian="Мама хоче, щоб я більше вчився.",
            ),
            Example(
                spanish="Espero que te guste el regalo.",
                ukrainian="Сподіваюся, що тобі сподобається подарунок.",
            ),
            Example(
                spanish="Necesito que me ayudes.", ukrainian="Мені потрібно, щоб ти мені допоміг."
            ),
            Example(spanish="Prefiero comer en casa.", ukrainian="Я волію їсти вдома."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Mis padres quieren que yo ___ en casa.",
            translation="Мої батьки хочуть, щоб я їв удома.",
            options=("coma", "como"),
            answer="coma",
            note="Після quieren que стоїть subjuntivo: coma.",
        ),
        Exercise(
            id="e2",
            sentence="Necesito que tú me ___ con esto.",
            translation="Мені потрібно, щоб ти допоміг мені з цим.",
            options=("ayudes", "ayudas"),
            answer="ayudes",
            note="Після necesito que стоїть subjuntivo: ayudes.",
        ),
        Exercise(
            id="e3",
            sentence="Yo quiero ___ a la playa este verano.",
            translation="Я хочу поїхати на пляж цього літа.",
            options=("ir", "voy"),
            answer="ir",
            note="Підмет той самий, тому інфінітив.",
        ),
        Exercise(
            id="e4",
            sentence="Espero que mañana no ___ frío.",
            translation="Сподіваюся, що завтра не буде холодно.",
            options=("haga", "hace"),
            answer="haga",
            note="Після espero que стоїть subjuntivo: haga.",
        ),
        Exercise(
            id="e5",
            sentence="Prefiero que tú ___ (salir) más temprano.",
            translation="Я волію, щоб ти виходив раніше.",
            options=(),
            answer="salgas",
            note="Основа з форми yo salgo: salgas.",
        ),
        Exercise(
            id="e6",
            sentence="Quiero que tú ___ (ser) feliz.",
            translation="Я хочу, щоб ти був щасливий.",
            options=(),
            answer="seas",
            note="Ser має неправильний subjuntivo: seas.",
        ),
    ),
)
