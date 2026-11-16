from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="mucho_poco",
    level="A1",
    order=85,
    title="mucho, poco, bastante: багато, мало, досить",
    lesson=Lesson(
        points=(
            "Mucho («багато»), poco («мало») і bastante («достатньо» або «досить багато») стоять перед іменником і кажуть, скільки його: mucho dinero, poco tiempo, bastante pan.",
            "Mucho і poco узгоджуються з іменником у роді й числі: mucho, mucha, muchos, muchas; poco, poca, pocos, pocas: muchos amigos, poca leche.",
            "Bastante змінюється лише за числом: bastante dinero, bastantes problemas.",
            "З незлічуваним іменником (dinero, tiempo, leche, agua, gente) ставимо однину: mucho dinero, poca agua. Слово gente — збірне, в однині й жіночого роду: mucha gente. Agua жіночого роду, хоч і el agua: mucha agua. З лічильним іменником ставимо множину: muchos amigos, pocas casas.",
            "Так само з hay: hay poca leche. Про погоду кажуть hace mucho calor, hace mucho frío — це готові вирази. Перед прикметником і прислівником кажемо muy, а не mucho: muy grande, muy bien.",
        ),
        examples=(
            Example(
                spanish="Tengo muchos amigos en España.",
                ukrainian="У мене багато друзів в Іспанії.",
            ),
            Example(spanish="Hace mucho calor.", ukrainian="Дуже спекотно."),
            Example(
                spanish="Hay poca leche en la nevera.", ukrainian="У холодильнику мало молока."
            ),
            Example(spanish="Hay bastante dinero.", ukrainian="Грошей достатньо."),
            Example(
                spanish="Tenemos bastantes problemas.", ukrainian="У нас досить багато проблем."
            ),
            Example(spanish="Hay mucha gente en la calle.", ukrainian="На вулиці багато людей."),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Tengo ___ amigas en Madrid.",
            translation="У мене багато подруг у Мадриді.",
            options=("muchas", "muchos"),
            answer="muchas",
            note="Amigas — жіночий рід, множина: muchas.",
        ),
        Exercise(
            id="e2",
            sentence="En la mesa hay ___ pan.",
            translation="На столі мало хліба.",
            options=("poco", "poca"),
            answer="poco",
            note="Pan — чоловічого роду, однина: poco.",
        ),
        Exercise(
            id="e3",
            sentence="En la tienda hay ___ gente.",
            translation="У магазині мало людей.",
            options=("poco", "poca"),
            answer="poca",
            note="Gente — однина жіночого роду: poca.",
        ),
        Exercise(
            id="e4",
            sentence="Necesito ___ tiempo para estudiar.",
            translation="Мені потрібно досить багато часу, щоб вчитися.",
            options=("bastante", "bastantes"),
            answer="bastante",
            note="Tiempo в однині: bastante.",
        ),
        Exercise(
            id="e5",
            sentence="En la clase hay ___ alumnos.",
            translation="У класі багато учнів.",
            options=(),
            answer="muchos",
            note="Alumnos — чоловічий рід, множина: muchos.",
        ),
        Exercise(
            id="e6",
            sentence="Tenemos ___ problemas.",
            translation="У нас мало проблем.",
            options=(),
            answer="pocos",
            note="Problemas — чоловічий рід, множина: pocos.",
        ),
    ),
)
