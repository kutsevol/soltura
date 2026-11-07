from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="verb_preposition",
    level="B1",
    order=60,
    title="Дієслова з прийменниками: pensar en, soñar con",
    lesson=Lesson(
        points=(
            "Багато дієслів вимагають певного прийменника, який не збігається з українським: pensar en (думати про), soñar con (мріяти про), depender de (залежати від), acordarse de (пам’ятати про), casarse con (одружитися з), enamorarse de (закохатися в).",
            "З інфінітивом: empezar a, volver a, aprender a, ayudar a; а також terminar de, dejar de, acabar de. Acabar de + інфінітив означає «щойно зробити»: acabo de llegar.",
            "Прийменник стоїть і перед питальним словом: ¿en qué piensas?, ¿de qué depende?",
            "Вчіть дієслово разом із прийменником, як одне ціле.",
        ),
        examples=(
            Example(
                spanish="Pienso en mis padres todos los días.",
                ukrainian="Я думаю про батьків щодня.",
            ),
            Example(spanish="Sueño con vivir en la playa.", ukrainian="Я мрію жити біля моря."),
            Example(spanish="Todo depende de ti.", ukrainian="Усе залежить від тебе."),
            Example(
                spanish="He empezado a estudiar español.", ukrainian="Я почав вчити іспанську."
            ),
            Example(spanish="Dejé de fumar hace un año.", ukrainian="Я кинув курити рік тому."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="¿___ quién te casaste?",
            translation="З ким ти одружився?",
            options=("Con", "De", "En"),
            answer="Con",
            note="Casarse вимагає con: casarse con.",
        ),
        Exercise(
            id="e2",
            sentence="Me he enamorado ___ ella.",
            translation="Я закохався в неї.",
            options=("de", "con"),
            answer="de",
            note="Enamorarse вимагає de: enamorarse de.",
        ),
        Exercise(
            id="e3",
            sentence="Mi decisión depende ___ muchas cosas.",
            translation="Моє рішення залежить від багатьох речей.",
            options=("de", "en"),
            answer="de",
            note="Depender вимагає de: depender de.",
        ),
        Exercise(
            id="e4",
            sentence="Empecé ___ aprender italiano el año pasado.",
            translation="Минулого року я почав вчити італійську.",
            options=("a", "de"),
            answer="a",
            note="Empezar вимагає a перед інфінітивом: empezar a.",
        ),
        Exercise(
            id="e5",
            sentence="Acabo ___ llegar a casa.",
            translation="Я щойно прийшов додому.",
            options=("de", "a"),
            answer="de",
            note="Acabar вимагає de перед інфінітивом: acabo de llegar.",
        ),
        Exercise(
            id="e6",
            sentence="Mi madre se acuerda ___ todo.",
            translation="Моя мама все пам’ятає.",
            options=("de", "con"),
            answer="de",
            note="Acordarse вимагає de: acordarse de.",
        ),
    ),
)
