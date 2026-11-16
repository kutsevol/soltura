from soltura.grammar.units import Example, Exercise, GrammarUnit, Lesson

UNIT = GrammarUnit(
    id="possessives",
    level="A1",
    order=75,
    title="Присвійні: mi, tu, su, nuestro, vuestro",
    lesson=Lesson(
        points=(
            "Присвійні кажуть, чиє: mi (мій, моя), tu (твій, твоя), su (його, її, Ваш, їхній), nuestro (наш), vuestro (ваш, коли кажемо «ти» кільком людям).",
            "Mi, tu і su узгоджуються з предметом за числом, а за родом не змінюються: mi libro, mi casa, mis libros, mis casas. Nuestro і vuestro змінюються і за родом, і за числом: nuestro libro, nuestra casa, nuestros libros, nuestras casas.",
            "Узгоджуємо з тим, що належить, а не з власником: nuestra casa, бо casa — жіночого роду, незалежно від того, хто там живе.",
            "Присвійне стоїть перед іменником і без артикля: mi libro, а не el mi libro і не libro mi.",
            "Su може означати його, її, Ваш або їхній. Хто саме, видно з контексту; щоб уточнити, замість su кажемо артикль, іменник і de él, de ella, de usted, de ellos, de ellas: la casa de ella.",
            "Tu (твій) пишемо без наголосу, а tú (ти) — з наголосом: tu casa, tú vives.",
            "Mi, tu, su самі по собі не стоять: на питання «¿De quién es este libro?» відповідаємо Es mi libro або Es de María, а не просто Mi.",
        ),
        examples=(
            Example(spanish="Mi hermana vive en Madrid.", ukrainian="Моя сестра живе в Мадриді."),
            Example(spanish="Tus libros están en la mesa.", ukrainian="Твої книжки на столі."),
            Example(
                spanish="Su casa es grande.", ukrainian="Його / її / їхній / Ваш будинок великий."
            ),
            Example(
                spanish="Nuestra casa está cerca del parque.",
                ukrainian="Наш будинок поруч із парком.",
            ),
            Example(spanish="¿Dónde están vuestros hijos?", ukrainian="Де ваші діти?"),
            Example(
                spanish="¿De quién es este libro? Es mi libro.",
                ukrainian="Чия це книга? Це моя книга.",
            ),
        ),
    ),
    exercises=(
        Exercise(
            id="e1",
            sentence="___ amigo se llama Pedro.",
            translation="Мого друга звати Педро.",
            options=("Mi", "Mis"),
            answer="Mi",
            note="Amigo в однині: mi.",
        ),
        Exercise(
            id="e2",
            sentence="___ padres viven en Valencia.",
            translation="Мої батьки живуть у Валенсії.",
            options=("Mi", "Mis"),
            answer="Mis",
            note="Padres у множині: mis.",
        ),
        Exercise(
            id="e3",
            sentence="Ana, ¿dónde vive ___ madre?",
            translation="Ано, де живе твоя мама?",
            options=("tu", "tus"),
            answer="tu",
            note="Madre в однині: tu. Присвійне tu — без наголосу, на відміну від tú («ти»).",
        ),
        Exercise(
            id="e4",
            sentence="Chicos, ¿dónde están ___ mochilas?",
            translation="Діти, де ваші рюкзаки?",
            options=("vuestras", "vuestros"),
            answer="vuestras",
            note="Mochilas — жіночий рід, множина: vuestras.",
        ),
        Exercise(
            id="e5",
            sentence="Nosotros vivimos en Valencia. ___ hijos van aquí al colegio.",
            translation="Ми живемо у Валенсії. Наші діти ходять тут до школи.",
            options=(),
            answer="Nuestros",
            note="Hijos — чоловічий рід, множина: nuestros.",
        ),
        Exercise(
            id="e6",
            sentence="Marta tiene un gato. ___ gato se llama Max.",
            translation="У Марти є кіт. Її кота звати Макс.",
            options=(),
            answer="Su",
            note="Su не змінюється за родом власника: su gato — її кіт.",
        ),
    ),
)
