from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    label: str
    prompt: str
    situations: tuple[str, ...]


TOPICS: list[Topic] = [
    Topic(
        label="Оренда житла",
        prompt="alquilar un piso",
        situations=(
            "viewing a flat with the landlord and asking about the contract",
            "discussing the deposit and the monthly rent by phone",
            "a problem in the flat: the heating does not work",
            "answering an advert from someone looking for a flatmate",
            "moving in and meeting the neighbours",
            "reading the rental contract and asking what a clause means",
            "the landlord comes to fix a leak",
            "deciding between two flats",
        ),
    ),
    Topic(
        label="У лікаря",
        prompt="una visita al médico",
        situations=(
            "booking an appointment at the health centre by phone",
            "describing a sore throat and a fever to the doctor",
            "the pharmacy: buying medicine with a prescription",
            "a child's check-up at the paediatrician",
            "the waiting room, where the appointment time was misunderstood",
            "getting the results of a blood test",
            "an emergency visit after a small accident",
            "asking the doctor for a sick-leave note",
        ),
    ),
    Topic(
        label="Покупки",
        prompt="ir de compras al supermercado",
        situations=(
            "finding a product and asking an assistant for help",
            "the self-checkout does not work",
            "comparing prices and choosing between two brands",
            "buying fruit and vegetables at a market stall",
            "returning a product with the receipt",
            "planning a dinner for guests and writing the list",
            "the fish counter and the baker's",
            "paying with a card that is declined",
        ),
    ),
    Topic(
        label="Документи",
        prompt="los trámites: el NIE y el empadronamiento",
        situations=(
            "booking an appointment online for the NIE",
            "registering the address at the town hall (empadronamiento)",
            "a missing document at the counter, so coming back another day",
            "asking a clerk which form is needed",
            "waiting in the queue and talking to the person beside you",
            "receiving a certificate by post",
            "a mistake in the name on a document",
            "opening a bank account, where the bank asks for the NIE",
        ),
    ),
    Topic(
        label="Сусіди й бар",
        prompt="los vecinos y el bar del barrio",
        situations=(
            "ordering breakfast at the bar and chatting with the waiter",
            "a neighbour complains about the noise",
            "meeting a neighbour in the lift",
            "the community meeting of the building",
            "a neighbour asks to borrow something",
            "watching a football match at the bar",
            "paying the bill and disagreeing about the total",
            "a neighbour's birthday",
        ),
    ),
]


def find_topic(prompt: str) -> Topic | None:
    return next((topic for topic in TOPICS if topic.prompt == prompt), None)
