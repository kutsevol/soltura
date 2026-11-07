from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="indefinido_vs_imperfecto",
    level="B1",
    order=10,
    title="indefinido чи imperfecto",
    lesson=Lesson(
        points=(
            "Indefinido (hablé, comí, viví) — завершена дія в минулому: ayer comí paella. Дія почалася й закінчилася, її можна назвати як подію.",
            "Imperfecto (hablaba, comía, vivía) — тло, звичка, дія без вказаного кінця: de niño vivía en un pueblo, todos los días iba al colegio.",
            "Imperfecto для опису: era alto, hacía frío, tenía el pelo largo. Indefinido для подій, що рухають розповідь: entró, se sentó, abrió la puerta.",
            "Слова-підказки зазвичай такі: ayer, anoche, de repente, una vez — indefinido; siempre, todos los días, normalmente, de niño — imperfecto. Але вирішує сенс: завершена подія чи тло.",
            "У розповіді вони чергуються: mientras yo cocinaba, sonó el teléfono. Imperfecto — тло, indefinido — подія.",
            "В imperfecto неправильні лише ir (iba), ser (era) і ver (veía).",
        ),
        examples=(
            Example(
                spanish="Ayer comí paella con mis amigos.", ukrainian="Вчора я їв паелью з друзями."
            ),
            Example(
                spanish="De niño vivía en un pueblo pequeño.",
                ukrainian="У дитинстві я жив у маленькому селі.",
            ),
            Example(spanish="Hacía frío y llovía.", ukrainian="Було холодно й ішов дощ."),
            Example(
                spanish="Cuando llegué, mi madre cocinaba.",
                ukrainian="Коли я прийшов, мама готувала.",
            ),
            Example(
                spanish="Todos los veranos íbamos a la playa.",
                ukrainian="Щоліта ми їздили на пляж.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Anoche ___ pizza en casa y luego vi una película.",
            translation="Вчора ввечері я з’їв піцу вдома, а потім дивився фільм.",
            options=("comí", "comía"),
            answer="comí",
            note="Дія завершилась, і за нею йде наступна подія: indefinido.",
        ),
        Exercise(
            id="e2",
            sentence="De niño, todos los días ___ al colegio andando.",
            translation="Щодня я ходив до школи пішки.",
            options=("iba", "fui"),
            answer="iba",
            note="Todos los días — звичка, тому imperfecto.",
        ),
        Exercise(
            id="e3",
            sentence="De repente, alguien ___ la puerta.",
            translation="Раптом хтось відчинив двері.",
            options=("abrió", "abría"),
            answer="abrió",
            note="De repente — подія, тому indefinido.",
        ),
        Exercise(
            id="e4",
            sentence="Mientras ___ (leer, yo) en el parque, empezó a llover.",
            translation="Поки я читав у парку, почався дощ.",
            options=("leía", "leí"),
            answer="leía",
            note="Mientras + дія-тло: imperfecto.",
        ),
        Exercise(
            id="e5",
            sentence="Ayer ___ (ir, yo) al médico.",
            translation="Вчора я сходив до лікаря.",
            options=(),
            answer="fui",
            note="Ayer — завершена дія, тому indefinido: fui.",
        ),
        Exercise(
            id="e6",
            sentence="En aquella foto mi abuela ___ (tener) el pelo largo.",
            translation="На тому фото в моєї бабусі було довге волосся.",
            options=(),
            answer="tenía",
            note="Опис — це imperfecto: tenía.",
        ),
    ),
)
