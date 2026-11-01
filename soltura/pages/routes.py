from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from soltura.templating import templates

router = APIRouter()


@router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "help.html")
