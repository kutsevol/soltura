from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="numbers",
    level="A1",
    order=80,
    title="Числівники: dos, quince, doscientos, tercero",
    lesson=Lesson(
        points=(
            "Від 0 до 15: cero, uno, dos, tres, cuatro, cinco, seis, siete, ocho, nueve, diez, once, doce, trece, catorce, quince.",
            "Від 16 до 29 числівник пишемо одним словом: dieciséis, diecisiete, dieciocho, diecinueve, veinte, veintiuno, veintidós, veintitrés, veintiséis. З 31 слова окремі, між десятками й одиницями стоїть y: treinta y uno, cuarenta y cinco.",
            "Десятки: treinta, cuarenta, cincuenta, sesenta, setenta, ochenta, noventa. Сотні: cien (100, також cien mil), від 101 ciento (ciento diez), doscientos, trescientos, cuatrocientos, quinientos, seiscientos, setecientos, ochocientos, novecientos. Тисяча — mil: dos mil.",
            "Uno перед іменником стає un або una: un libro, una mesa; так само складені з ним: veintiún libros, treinta y una personas. Числівники dos, tres, cuatro і далі за родом не змінюються: dos libros, dos mesas.",
            "Сотні від 200 узгоджуються з іменником у роді: doscientos euros, doscientas personas.",
            "Порядкові до десятого: primero, segundo, tercero, cuarto, quinto, sexto, séptimo, octavo, noveno, décimo. Вони змінюються за родом: el segundo día, la tercera clase. Primero і tercero перед чоловічим іменником в однині скорочуються: el primer día, el tercer piso.",
        ),
        examples=(
            Example(
                spanish="Hay treinta y cinco alumnos en la clase.",
                ukrainian="У класі тридцять п’ять учнів.",
            ),
            Example(spanish="Tengo un hermano y una hermana.", ukrainian="У мене є брат і сестра."),
            Example(spanish="Son cuarenta euros.", ukrainian="Це сорок євро."),
            Example(spanish="Aquí viven doscientas personas.", ukrainian="Тут живе двісті людей."),
            Example(
                spanish="Mi hermana tiene veintidós años.",
                ukrainian="Моїй сестрі двадцять два роки.",
            ),
            Example(
                spanish="Hoy es mi primera clase de español.",
                ukrainian="Сьогодні мій перший урок іспанської.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Tengo un perro y ___ gata.",
            translation="У мене є собака й кішка.",
            options=("una", "un"),
            answer="una",
            note="Gata — жіночого роду: una.",
        ),
        Exercise(
            id="e2",
            sentence="Son ___ euros.",
            translation="Це двісті євро.",
            options=("doscientos", "doscientas"),
            answer="doscientos",
            note="Euros — чоловічий рід: doscientos.",
        ),
        Exercise(
            id="e3",
            sentence="En la fiesta hay ___ personas.",
            translation="На вечірці двісті людей.",
            options=("doscientos", "doscientas"),
            answer="doscientas",
            note="Personas — жіночий рід: doscientas.",
        ),
        Exercise(
            id="e4",
            sentence="Mi hermano tiene ___ años.",
            translation="Моєму братові шістнадцять років.",
            options=("dieciséis", "dieciseis"),
            answer="dieciséis",
            note="Dieciséis пишемо одним словом, з наголосом на останньому складі.",
        ),
        Exercise(
            id="e5",
            sentence="Es mi ___ clase de español.",
            translation="Це мій третій урок іспанської.",
            options=(),
            answer="tercera",
            note="Clase — жіночий рід, тож tercera.",
        ),
        Exercise(
            id="e6",
            sentence="Cuatro más cinco son ___.",
            translation="Чотири плюс п’ять — дев’ять.",
            options=(),
            answer="nueve",
            note="4 + 5 = 9 (más — плюс): nueve.",
        ),
    ),
)
