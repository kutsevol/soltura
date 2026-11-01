from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import current_learner
from soltura.learner.models import Learner, LexemeStatus
from soltura.learner.repository import get_saved_words
from soltura.llm.client import LLMClient, get_llm
from soltura.reading.service import save_tapped_word
from soltura.templating import templates
from soltura.words.service import MAX_WORDS, Problem, look_up_words, parse_words

router = APIRouter(prefix="/words")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LearnerDep = Annotated[Learner, Depends(current_learner)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]

STATUS_LABEL = {LexemeStatus.LEARNING: "Вивчаю", LexemeStatus.KNOWN: "Знаю"}
PROBLEM_LABEL = {
    Problem.MULTIPLE_WORDS: "введіть одне слово в рядку.",
    Problem.NOT_SPANISH: "не схоже на іспанське слово, перевірте написання.",
    Problem.NO_EXAMPLE: "не вдалося підібрати приклад, спробуйте ще раз.",
    Problem.UNAVAILABLE: "модель зараз недоступна, спробуйте ще раз.",
}
MAX_LEMMA_LENGTH = 64
MAX_SENTENCE_LENGTH = 500


def due_label(due: datetime, now: datetime) -> str:
    return "зараз" if due <= now else due.astimezone(UTC).strftime("%d.%m.%Y")


def _learner_id(learner: Learner) -> int:
    if learner.id is None:
        raise ValueError("current_learner returned an unsaved learner")
    return learner.id


def _message(request: Request, text: str) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "words/message.html",
        {"message": text},
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def _words_context(session: AsyncSession, learner: Learner, search: str) -> dict[str, object]:
    return {
        "words": await get_saved_words(session, _learner_id(learner), search.strip()),
        "search": search.strip(),
        "now": datetime.now(UTC),
        "due_label": due_label,
        "status_label": STATUS_LABEL,
    }


@router.get("", response_class=HTMLResponse)
async def words_page(
    request: Request, session: SessionDep, learner: LearnerDep, q: str = ""
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "words.html", await _words_context(session, learner, q)
    )


@router.get("/search", response_class=HTMLResponse)
async def search_words(
    request: Request, session: SessionDep, learner: LearnerDep, q: str = ""
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "words/list.html", await _words_context(session, learner, q)
    )


@router.post("/lookup", response_class=HTMLResponse)
async def lookup_words(
    request: Request,
    session: SessionDep,
    learner: LearnerDep,
    llm: LLMDep,
    words: Annotated[str, Form()] = "",
) -> HTMLResponse:
    lines = parse_words(words)
    if not lines:
        return _message(request, "Введіть слово.")
    if len(lines) > MAX_WORDS:
        return _message(request, f"Не більше {MAX_WORDS} слів за раз.")
    results = await look_up_words(session, llm, _learner_id(learner), lines)
    return templates.TemplateResponse(
        request, "words/preview.html", {"results": results, "problem_label": PROBLEM_LABEL}
    )


@router.post("/add", response_class=HTMLResponse)
async def add_words(
    request: Request,
    session: SessionDep,
    learner: LearnerDep,
    lemma: Annotated[list[str] | None, Form()] = None,
    sentence: Annotated[list[str] | None, Form()] = None,
) -> HTMLResponse:
    lemmas, sentences = lemma or [], sentence or []
    pairs = list(zip(lemmas, sentences, strict=False))
    if (
        not 0 < len(lemmas) <= MAX_WORDS
        or len(lemmas) != len(sentences)
        or any(not 0 < len(item.strip()) <= MAX_LEMMA_LENGTH for item, _ in pairs)
        or any(not 0 < len(text.strip()) <= MAX_SENTENCE_LENGTH for _, text in pairs)
    ):
        return _message(request, "Не вдалося зберегти: перевірте слова й спробуйте ще раз.")
    now = datetime.now(UTC)
    for item, text in pairs:
        await save_tapped_word(session, _learner_id(learner), item, text, now)
    response = templates.TemplateResponse(
        request, "words/added.html", {"lemmas": [item.strip().lower() for item in lemmas]}
    )
    response.headers["HX-Trigger"] = "wordsChanged"
    return response
