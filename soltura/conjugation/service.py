from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.conjugation.forms import Person, Tense, conjugate
from soltura.conjugation.units import (
    introduced_sets,
    next_unit_set,
    parse_unit_key,
    unit_keys,
)
from soltura.learner.models import (
    KnowledgeType,
    MemoryCard,
    Rating,
    ReviewSource,
    UnitKind,
)
from soltura.learner.repository import (
    count_unreviewed_cards,
    get_unit_keys,
    get_verb_lemmas,
)
from soltura.practice.checking import SpanishCheck, check_spanish
from soltura.srs.service import due_queue, review, schedule_units

SESSION_SIZE = 18

# The ending is what is being learned: a missing accent is a slip, a changed letter is
# another form (tuvieron against tuvieran) and does not pass.
CONJUGATION_RATING = {
    SpanishCheck.EXACT: Rating.GOOD,
    SpanishCheck.ACCENT_SLIP: Rating.HARD,
    SpanishCheck.TYPO: Rating.AGAIN,
    SpanishCheck.OTHER_FORM: Rating.AGAIN,
    SpanishCheck.WRONG: Rating.AGAIN,
}


@dataclass(frozen=True)
class ConjugationItem:
    card_id: int
    verb: str
    tense: Tense
    person: Person


@dataclass(frozen=True)
class ConjugationResult:
    rating: Rating
    check: SpanishCheck
    expected: str


async def build_session(
    session: AsyncSession, learner_id: int, now: datetime
) -> list[ConjugationItem]:
    # One verb in one tense at a time: the next set of six arrives only once the last
    # one has been answered, so the learner is never holding two sets they have not met.
    if await count_unreviewed_cards(session, learner_id, UnitKind.CONJUGATION) == 0:
        introduced = introduced_sets(await get_unit_keys(session, learner_id, UnitKind.CONJUGATION))
        next_set = next_unit_set(await get_verb_lemmas(session), introduced)
        if next_set is not None:
            await schedule_units(
                session,
                learner_id,
                UnitKind.CONJUGATION,
                unit_keys(next_set),
                KnowledgeType.RECALL,
                now,
            )

    cards = await due_queue(
        session, learner_id, now=now, limit=SESSION_SIZE, unit_kind=UnitKind.CONJUGATION
    )
    items: list[ConjugationItem] = []
    for card in cards:
        parsed = parse_unit_key(card.unit_key)
        if card.id is not None and parsed is not None:
            items.append(ConjugationItem(card.id, *parsed))
    return items


async def answer_item(
    session: AsyncSession,
    learner_id: int,
    card_id: int,
    answer: str,
    duration_ms: int | None,
    now: datetime,
) -> ConjugationResult:
    card = await session.get(MemoryCard, card_id)
    if card is None or card.learner_id != learner_id or card.unit_kind != UnitKind.CONJUGATION:
        raise PermissionError("This card does not belong to the learner")
    parsed = parse_unit_key(card.unit_key)
    expected = conjugate(*parsed) if parsed is not None else None
    if parsed is None or expected is None:
        raise ValueError(f"Card {card_id} does not name a form that can be conjugated")

    check = check_spanish(answer, expected, parsed[0])
    rating = CONJUGATION_RATING[check]
    await review(
        session,
        card,
        rating,
        ReviewSource.CONJUGATION,
        now,
        answer=answer.strip() or None,
        duration_ms=duration_ms,
    )
    return ConjugationResult(rating=rating, check=check, expected=expected)
