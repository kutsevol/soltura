from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import UnitKind
from soltura.learner.repository import (
    count_due_cards,
    count_learning_words,
    get_latest_placement_run,
)
from soltura.use_cases.grammar import next_lesson
from soltura.use_cases.study import StudyProgress, open_session
from soltura.words.vocabulary import VocabularyMap, build_vocabulary_map


@dataclass(frozen=True)
class HubSummary:
    due: int
    learning: int
    conjugation_due: int
    grammar_due: int
    grammar_next: str | None
    placement_rank: int | None
    vocabulary: VocabularyMap
    study: StudyProgress | None = None


async def hub_summary(session: AsyncSession, learner_id: int, now: datetime) -> HubSummary:
    placement = await get_latest_placement_run(session, learner_id)
    lesson = await next_lesson(session, learner_id)
    return HubSummary(
        due=await count_due_cards(session, learner_id, now, UnitKind.WORD),
        learning=await count_learning_words(session, learner_id),
        conjugation_due=await count_due_cards(session, learner_id, now, UnitKind.CONJUGATION),
        grammar_due=await count_due_cards(session, learner_id, now, UnitKind.GRAMMAR),
        grammar_next=lesson.title if lesson else None,
        placement_rank=placement.known_rank if placement else None,
        vocabulary=await build_vocabulary_map(session, learner_id),
        study=await open_session(session, learner_id, now),
    )
