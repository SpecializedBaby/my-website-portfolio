"""FastAPI application for the portfolio site.

Content is loaded once at startup and cached on ``app.state``. Routes render Jinja2
templates over that content. No database, no auth.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.content import load_all

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
CONTENT_DIR = PROJECT_DIR / "content"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
RESUME_PATH = STATIC_DIR / "resume.pdf"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load + validate content once. A bad content file raises here and fails the boot.
    app.state.content = load_all(CONTENT_DIR)
    app.state.has_resume = RESUME_PATH.is_file()
    yield


app = FastAPI(title="Portfolio — Dmytro Kostevskyi", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _base_context(request: Request) -> dict:
    content = request.app.state.content
    return {
        "request": request,
        "site": content.site,
        "profile": content.site.profile,
        "has_resume": request.app.state.has_resume,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    content = request.app.state.content
    ctx = _base_context(request)
    ctx["posts"] = content.posts
    return templates.TemplateResponse(request, "index.html", ctx)


@app.get("/posts/{slug}", response_class=HTMLResponse)
async def post_detail(request: Request, slug: str) -> HTMLResponse:
    content = request.app.state.content
    post = content.post_by_slug(slug)
    if post is None:
        return _not_found(request)
    ctx = _base_context(request)
    ctx["post"] = post
    return templates.TemplateResponse(request, "post.html", ctx)


@app.get("/resume.pdf")
async def resume(request: Request):
    if not request.app.state.has_resume:
        return _not_found(request)
    return FileResponse(
        RESUME_PATH,
        media_type="application/pdf",
        filename="Dmytro-Kostevskyi-Resume.pdf",
    )


@app.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


def _not_found(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "404.html", _base_context(request), status_code=404)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc) -> HTMLResponse:
    return _not_found(request)
