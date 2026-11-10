import random
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.language.coverage import measure_coverage, words_to_replace
from soltura.language.frequency import UNRANKED
from soltura.language.nlp import analyze
from soltura.learner.models import KnowledgeType, Learner, MemoryCard, Rating, ReviewSource
from soltura.learner.models import Lexeme as LexemeRow
from soltura.learner.repository import (
    get_due_card,
    get_lexemes_by_lemmas,
    get_recent_titles,
    save_reading_text,
)
from soltura.llm.client import LLMClient
from soltura.reading.service import (
    GIST_SYSTEM,
    GLOSS_SYSTEM,
    MAX_SIMPLIFICATIONS,
    RECENT_TITLES,
    TARGET_COVERAGE,
    WRITER_SYSTEM,
    GeneratedText,
    GistVerdict,
    Gloss,
    PreparedText,
    TapResult,
    due_lemmas,
    first_draft_prompt,
    lemmas_counted_as_known,
    simplify_prompt,
    vocabulary_range,
)
from soltura.reading.topics import find_topic
from soltura.reading.variation import pick_variation, variation_prompt
from soltura.srs.service import review, save_word


async def prepare_text(
    session: AsyncSession,
    llm: LLMClient,
    learner: Learner,
    now: datetime,
    topic: str,
    source_text: str | None = None,
    rng: random.Random | None = None,
) -> PreparedText:
    if learner.id is None:
        raise ValueError("The learner must be saved before a text is prepared")
    vocabulary = await vocabulary_range(session, learner.id)
    known = await lemmas_counted_as_known(session, learner.id)
    due = await due_lemmas(session, learner.id, now)
    variation = ""
    if source_text is None:
        # A pasted text is adapted as it is; only a text written from a topic is varied.
        preset = find_topic(topic)
        picked = pick_variation(preset.situations if preset else (), rng or random.Random())
        recent = await get_recent_titles(session, learner.id, RECENT_TITLES)
        variation = variation_prompt(picked, recent)

    draft = await llm(
        GeneratedText,
        system=WRITER_SYSTEM,
        prompt=first_draft_prompt(vocabulary, topic, due, source_text, variation),
        effort="medium",
    )
    attempts = 1
    coverage = measure_coverage(analyze(f"{draft.title}. {draft.text}"), known)
    while coverage.ratio < TARGET_COVERAGE and attempts <= MAX_SIMPLIFICATIONS:
        ranks = {
            lexeme.lemma: lexeme.frequency_rank
            for lexeme in await get_lexemes_by_lemmas(session, coverage.unknown_lemmas)
        }
        rare = words_to_replace(coverage, ranks, TARGET_COVERAGE)
        draft = await llm(
            GeneratedText,
            system=WRITER_SYSTEM,
            prompt=simplify_prompt(vocabulary, draft, rare, due),
            effort="medium",
        )
        attempts += 1
        coverage = measure_coverage(analyze(f"{draft.title}. {draft.text}"), known)

    await save_reading_text(session, learner.id, topic or None, draft.title)
    await session.commit()
    return PreparedText(
        title=draft.title,
        text=draft.text,
        coverage=coverage.ratio,
        attempts=attempts,
        below_target=coverage.ratio < TARGET_COVERAGE,
        unknown_lemmas=coverage.unknown_lemmas,
    )


async def tap_word(
    session: AsyncSession,
    llm: LLMClient,
    learner_id: int,
    word: str,
    sentence: str,
    now: datetime,
) -> TapResult:
    gloss = await llm(
        Gloss,
        system=GLOSS_SYSTEM,
        prompt=f"Word: {word}\nSentence: {sentence}",
        effort="low",
        max_tokens=4_000,
    )
    lemma = gloss.lemma.strip().lower()
    reviewed = False
    lexemes = await get_lexemes_by_lemmas(session, [lemma])
    if lexemes and lexemes[0].id is not None:
        # Looking a due word up is a failed recognition, the only signal reading gives.
        card = await get_due_card(session, learner_id, lexemes[0].id, KnowledgeType.RECOGNIZE, now)
        if card is not None:
            await review(session, card, Rating.AGAIN, ReviewSource.READING_TAP, now)
            reviewed = True
    return TapResult(word=word, lemma=lemma, translation=gloss.translation, reviewed=reviewed)


async def save_tapped_word(
    session: AsyncSession,
    learner_id: int,
    lemma: str,
    sentence: str,
    now: datetime,
    topic: str | None = None,
) -> list[MemoryCard]:
    lemma = lemma.strip().lower()
    # The LLM's lemma can be one the frequency seed never ranked; it still gets a
    # lexeme, at the bottom of the frequency order, so the word can be learned.
    await session.execute(
        insert(LexemeRow)
        .values(lemma=lemma, pos="X", frequency_rank=UNRANKED)
        .on_conflict_do_nothing(index_elements=["lemma"])
    )
    [lexeme] = await get_lexemes_by_lemmas(session, [lemma])
    if lexeme.id is None:
        raise ValueError(f"Lexeme for {lemma!r} has no id")
    return await save_word(session, learner_id, lexeme.id, sentence, now, topic)


async def check_gist(llm: LLMClient, text: str, answer: str) -> GistVerdict:
    return await llm(
        GistVerdict,
        system=GIST_SYSTEM,
        prompt=f"Text:\n{text}\n\nLearner's answer: {answer}",
        effort="low",
        max_tokens=4_000,
    )
