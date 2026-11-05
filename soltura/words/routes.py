from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import LearnerIdDep
from soltura.llm.client import LLMClient, get_llm
from soltura.templating import templates
from soltura.words.service import (
    InvalidAddForm,
    InvalidLookup,
    add_words,
    find_saved_words,
    look_up_text,
)
from soltura.words.views import (
    ADD_FORM_MESSAGE,
    LOOKUP_MESSAGE,
    VocabularyView,
    preview_view,
    vocabulary_view,
    words_view,
)
from soltura.words.vocabulary import build_vocabulary_map

router = APIRouter(prefix="/words")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]


def _message(request: Request, text: str) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "words/message.html",
        {"message": text},
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def _words_context(session: AsyncSession, learner_id: int, search: str) -> dict[str, object]:
    words = await find_saved_words(session, learner_id, search)
    return vars(words_view(words, search, datetime.now(UTC)))


async def _vocabulary(session: AsyncSession, learner_id: int) -> VocabularyView:
    return vocabulary_view(await build_vocabulary_map(session, learner_id))


@router.get("", response_class=HTMLResponse)
async def words_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep, q: str = ""
) -> HTMLResponse:
    context = {
        **await _words_context(session, learner_id, q),
        "vocabulary": await _vocabulary(session, learner_id),
    }
    return templates.TemplateResponse(request, "words.html", context)


@router.get("/map", response_class=HTMLResponse)
async def vocabulary_map(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "words/map.html", {"vocabulary": await _vocabulary(session, learner_id)}
    )


@router.get("/search", response_class=HTMLResponse)
async def search_words(
    request: Request, session: SessionDep, learner_id: LearnerIdDep, q: str = ""
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "words/list.html", await _words_context(session, learner_id, q)
    )


@router.post("/lookup", response_class=HTMLResponse)
async def lookup_words(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    llm: LLMDep,
    words: Annotated[str, Form()] = "",
) -> HTMLResponse:
    try:
        results = await look_up_text(session, llm, learner_id, words)
    except InvalidLookup as error:
        return _message(request, LOOKUP_MESSAGE[error.problem])
    return templates.TemplateResponse(request, "words/preview.html", vars(preview_view(results)))


@router.post("/add", response_class=HTMLResponse)
async def add_words_route(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    lemma: Annotated[list[str] | None, Form()] = None,
    sentence: Annotated[list[str] | None, Form()] = None,
) -> HTMLResponse:
    try:
        lemmas = await add_words(
            session, learner_id, lemma or [], sentence or [], datetime.now(UTC)
        )
    except InvalidAddForm:
        return _message(request, ADD_FORM_MESSAGE)
    response = templates.TemplateResponse(request, "words/added.html", {"lemmas": lemmas})
    response.headers["HX-Trigger"] = "wordsChanged"
    return response
