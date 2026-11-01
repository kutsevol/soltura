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
from soltura.words.service import NotASpanishWordError, WordLookupFailedError, look_up_word

router = APIRouter(prefix="/words")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LearnerDep = Annotated[Learner, Depends(current_learner)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]

STATUS_LABEL = {LexemeStatus.LEARNING: "Вивчаю", LexemeStatus.KNOWN: "Знаю"}
MAX_LEMMA_LENGTH = 64
MAX_SENTENCE_LENGTH = 500


def due_label(due: datetime, now: datetime) -> str:
    return "зараз" if due <= now else due.astimezone(UTC).strftime("%d.%m.%Y")


def _learner_id(learner: Learner) -> int:
    if learner.id is None:
        raise ValueError("current_learner returned an unsaved learner")
    return learner.id


def _message(request: Request, text: str, status_code: int) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "words/message.html", {"message": text}, status_code=status_code
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
async def lookup_word(
    request: Request,
    session: SessionDep,
    learner: LearnerDep,
    llm: LLMDep,
    word: Annotated[str, Form()] = "",
) -> HTMLResponse:
    word = word.strip()
    if not word or len(word.split()) > 1 or len(word) > MAX_LEMMA_LENGTH:
        return _message(
            request, "Введіть одне іспанське слово.", status.HTTP_422_UNPROCESSABLE_CONTENT
        )
    try:
        lookup = await look_up_word(session, llm, _learner_id(learner), word)
    except NotASpanishWordError:
        return _message(
            request,
            f"«{word}» не схоже на іспанське слово. Перевірте написання.",
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    except WordLookupFailedError:
        return _message(
            request, "Не вдалося підібрати приклад. Спробуйте ще раз.", status.HTTP_502_BAD_GATEWAY
        )
    return templates.TemplateResponse(request, "words/preview.html", {"lookup": lookup})


@router.post("/add", response_class=HTMLResponse)
async def add_word(
    request: Request,
    session: SessionDep,
    learner: LearnerDep,
    lemma: Annotated[str, Form(min_length=1, max_length=MAX_LEMMA_LENGTH)],
    sentence: Annotated[str, Form(min_length=1, max_length=MAX_SENTENCE_LENGTH)],
) -> HTMLResponse:
    await save_tapped_word(session, _learner_id(learner), lemma, sentence, datetime.now(UTC))
    response = templates.TemplateResponse(
        request, "words/added.html", {"lemma": lemma.strip().lower()}
    )
    response.headers["HX-Trigger"] = "wordsChanged"
    return response
