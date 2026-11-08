from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="pluscuamperfecto",
    level="B1",
    order=25,
    title="Pluscuamperfecto: había comido",
    lesson=Lesson(
        points=(
            "Pluscuamperfecto складається з imperfecto від haber і дієприкметника: había comido, habías comido, había comido, habíamos comido, habíais comido, habían comido.",
            "Воно означає дію, що відбулася раніше за іншу минулу: cuando llegué, mi madre ya había salido — коли я прийшов, мама вже вийшла.",
            "Дієприкметник той самий, що в perfecto, зокрема неправильні: hecho, visto, escrito, dicho, abierto, puesto, vuelto.",
            "Часто стоїть з ya, todavía no і nunca: nunca había visto el mar, todavía no había terminado.",
            "Haber і дієприкметник стоять разом, займенник перед haber: ya lo había visto.",
        ),
        examples=(
            Example(
                spanish="Cuando llegué, mi madre ya había salido.",
                ukrainian="Коли я прийшов, мама вже вийшла.",
            ),
            Example(spanish="Nunca había visto el mar.", ukrainian="Я ніколи не бачив моря."),
            Example(
                spanish="Ya habíamos cenado cuando llamaste.",
                ukrainian="Ми вже повечеряли, коли ти зателефонував.",
            ),
            Example(
                spanish="No sabía que habías vuelto.", ukrainian="Я не знав, що ти повернувся."
            ),
            Example(
                spanish="Todavía no había abierto la carta.", ukrainian="Я ще не відкрив листа."
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="Cuando llegué al cine, la película ya ___.",
            translation="Коли я прийшов у кіно, фільм уже почався.",
            options=("había empezado", "he empezado"),
            answer="había empezado",
            note="Фільм почався раніше за мій прихід у минулому: pluscuamperfecto.",
        ),
        Exercise(
            id="e2",
            sentence="Cuando me llamaste, yo ya ___ la cena.",
            translation="Коли ти мені зателефонував, я вже приготував вечерю.",
            options=("había preparado", "habíamos preparado"),
            answer="había preparado",
            note="Підмет yo, тому había.",
        ),
        Exercise(
            id="e3",
            sentence="Mis padres nunca ___ en avión antes de aquel viaje.",
            translation="Мої батьки ніколи не літали літаком до тієї подорожі.",
            options=("habían viajado", "había viajado"),
            answer="habían viajado",
            note="Mis padres — вони, тому habían.",
        ),
        Exercise(
            id="e4",
            sentence="Ella ya ___ el correo cuando lo vi.",
            translation="Вона вже написала листа, коли я його побачив.",
            options=("había escrito", "he escrito"),
            answer="había escrito",
            note="Дія раніша за минулий момент (cuando lo vi), тому había escrito; escribir має неправильний дієприкметник escrito.",
        ),
        Exercise(
            id="e5",
            sentence="Nosotros todavía no ___ comido cuando llegaron.",
            translation="Ми ще не їли, коли вони прийшли.",
            options=(),
            answer="habíamos",
            note="Підмет nosotros, тому habíamos.",
        ),
        Exercise(
            id="e6",
            sentence="Cuando dieron la película en la tele, yo ya la ___ visto.",
            translation="Коли фільм показали по телевізору, я вже його бачив.",
            options=(),
            answer="había",
            note="Підмет yo, а дія раніша за минулий момент: había visto.",
        ),
    ),
)
