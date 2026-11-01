from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    label: str
    prompt: str


TOPICS: list[Topic] = [
    Topic(label="Оренда житла", prompt="alquilar un piso"),
    Topic(label="У лікаря", prompt="una visita al médico"),
    Topic(label="Покупки", prompt="ir de compras al supermercado"),
    Topic(label="Документи", prompt="los trámites: el NIE y el empadronamiento"),
    Topic(label="Сусіди й бар", prompt="los vecinos y el bar del barrio"),
]
