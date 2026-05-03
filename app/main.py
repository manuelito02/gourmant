import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings as app_settings
from app.i18n import SUPPORTED_LANGS, get_templates
from app.routers import admin, auth, recipes, uploads
from app.routers import settings as settings_router

UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", "/app/uploads"))
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Gourmant", description="Recipe management API", version="0.1.0")

app.add_middleware(SessionMiddleware, secret_key=app_settings.secret_key)

app.include_router(auth.router)
app.include_router(recipes.router)
app.include_router(uploads.router)
app.include_router(settings_router.router)
app.include_router(admin.router)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/dashboard", status_code=302)
    return get_templates(request).TemplateResponse(request, "index.html")


@app.post("/set-language", response_class=HTMLResponse)
def set_language(request: Request, lang: str = Form(...)):
    if lang in SUPPORTED_LANGS:
        request.session["lang"] = lang
    referer = request.headers.get("referer", "/")
    return RedirectResponse(referer, status_code=302)


@app.get("/health")
def health():
    return {"status": "ok"}
